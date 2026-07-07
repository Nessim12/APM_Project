import base64
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from accounts.models import User
from .models import (
    AlerteSSLEnvoyee,
    CanalAlerteChoices,
    CertificatSSL,
    NiveauAlerteChoices,
    NotificationAdmin,
)

logger = logging.getLogger(__name__)

NIVEAU_LABELS = {
    NiveauAlerteChoices.J60: 'Expiration sous 60 jours',
    NiveauAlerteChoices.J30: 'Expiration sous 30 jours',
    NiveauAlerteChoices.EXPIRE: 'Certificat expiré',
}

NIVEAU_PRIORITE = {
    NiveauAlerteChoices.EXPIRE: 3,
    NiveauAlerteChoices.J30: 2,
    NiveauAlerteChoices.J60: 1,
}


def get_admins():
    return User.objects.filter(
        role__in=[User.RoleChoices.ADMIN, User.RoleChoices.ADMIN_SYS],
        is_active=True,
    ).exclude(email='')


def _alert_context(certificat, niveau):
    return {
        'certificat': certificat,
        'niveau': niveau,
        'niveau_label': NIVEAU_LABELS[niveau],
        'jours_restants': certificat.jours_restants,
        'jours_restants_label': certificat.jours_restants_label,
        'renouvellement_label': certificat.renouvellement_label,
        'auto_renouvellement': certificat.auto_renouvellement,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }


def _should_send_alert(certificat, niveau, canal):
    try:
        alerte = AlerteSSLEnvoyee.objects.get(
            certificat=certificat,
            niveau=niveau,
            canal=canal,
        )
    except AlerteSSLEnvoyee.DoesNotExist:
        return True

    if niveau == NiveauAlerteChoices.EXPIRE:
        rappel = getattr(settings, 'SSL_ALERT_RAPPEL_JOURS', 7)
        return (timezone.now() - alerte.envoyee_le).days >= rappel

    return False


def _mark_alert_sent(certificat, niveau, canal):
    AlerteSSLEnvoyee.objects.update_or_create(
        certificat=certificat,
        niveau=niveau,
        canal=canal,
        defaults={'envoyee_le': timezone.now()},
    )


def _build_notification_message(certificat, niveau):
    renouvellement = certificat.renouvellement_label
    return (
        f"Application : {certificat.application.nom}\n"
        f"Domaine : {certificat.domaine}\n"
        f"Fournisseur SSL : {certificat.emetteur}\n"
        f"Expiration : {certificat.date_expiration.strftime('%d/%m/%Y')}\n"
        f"Jours restants : {certificat.jours_restants_label}\n"
        f"Renouvellement auto. : {renouvellement}"
    )


def _build_email_subject(certificat, niveau):
    prefix = '[APM SSL]'
    if niveau == NiveauAlerteChoices.EXPIRE:
        return f"{prefix} URGENT — Certificat expiré : {certificat.domaine}"
    if niveau == NiveauAlerteChoices.J30:
        return f"{prefix} Alerte 30j — {certificat.domaine}"
    return f"{prefix} Alerte 60j — {certificat.domaine}"


def send_email_alert(certificat, niveau, admins):
    if not _should_send_alert(certificat, niveau, CanalAlerteChoices.EMAIL):
        return 0

    context = _alert_context(certificat, niveau)
    subject = _build_email_subject(certificat, niveau)
    text_body = render_to_string('ssl/emails/ssl_alert.txt', context)
    html_body = render_to_string('ssl/emails/ssl_alert.html', context)
    recipients = [admin.email for admin in admins]

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        _mark_alert_sent(certificat, niveau, CanalAlerteChoices.EMAIL)
        logger.info('Alerte e-mail SSL envoyée (%s) pour %s', niveau, certificat.domaine)
        return len(recipients)
    except Exception as exc:
        logger.exception('Échec envoi e-mail SSL pour %s: %s', certificat.domaine, exc)
        return 0


def send_sms_alert(certificat, niveau, admins):
    if not getattr(settings, 'SMS_ENABLED', False):
        return 0

    if not _should_send_alert(certificat, niveau, CanalAlerteChoices.SMS):
        return 0

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')

    if not all([account_sid, auth_token, from_number]):
        logger.warning('SMS activé mais configuration Twilio incomplète.')
        return 0

    renouvellement = 'auto' if certificat.auto_renouvellement else 'manuel'
    body = (
        f"[APM SSL] {NIVEAU_LABELS[niveau]} — "
        f"{certificat.application.nom} / {certificat.domaine} — "
        f"{certificat.jours_restants_label} — Renouv. {renouvellement}"
    )

    sent = 0
    credentials = base64.b64encode(f'{account_sid}:{auth_token}'.encode()).decode()
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'

    for admin in admins:
        if not admin.telephone:
            continue
        data = urllib.parse.urlencode({
            'To': admin.telephone,
            'From': from_number,
            'Body': body[:1600],
        }).encode()
        request = urllib.request.Request(
            url,
            data=data,
            method='POST',
            headers={
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if 200 <= response.status < 300:
                    sent += 1
        except urllib.error.HTTPError as exc:
            logger.exception('Échec SMS Twilio pour %s: %s', admin.telephone, exc)
        except urllib.error.URLError as exc:
            logger.exception('Erreur réseau SMS pour %s: %s', admin.telephone, exc)

    if sent:
        _mark_alert_sent(certificat, niveau, CanalAlerteChoices.SMS)
    return sent


def _ensure_notification_for_admin(certificat, niveau, admin):
    titre = _build_email_subject(certificat, niveau).replace('[APM SSL] ', '')
    message = _build_notification_message(certificat, niveau)

    existing = NotificationAdmin.objects.filter(
        destinataire=admin,
        certificat=certificat,
        niveau=niveau,
    ).first()

    if existing:
        if existing.titre != titre or existing.message != message:
            existing.titre = titre
            existing.message = message
            existing.save(update_fields=['titre', 'message'])
        return False

    NotificationAdmin.objects.create(
        destinataire=admin,
        certificat=certificat,
        niveau=niveau,
        titre=titre,
        message=message,
        lue=False,
    )
    return True


def ensure_in_app_notifications(certificat=None):
    """Crée les notifications manquantes pour les certificats actuellement en alerte."""
    admins = list(get_admins())
    if not admins:
        return 0

    if certificat is not None:
        certificats = [certificat] if certificat.niveau_alerte_actuel() else []
    else:
        certificats = [item['certificat'] for item in get_certificats_en_alerte()]

    created = 0
    for cert in certificats:
        niveau = cert.niveau_alerte_actuel()
        if not niveau:
            continue
        cert_created = 0
        for admin in admins:
            if _ensure_notification_for_admin(cert, niveau, admin):
                cert_created += 1
        if cert_created:
            _mark_alert_sent(cert, niveau, CanalAlerteChoices.APP)
        created += cert_created
    return created


def create_in_app_notifications(certificat, niveau, admins):
    if not _should_send_alert(certificat, niveau, CanalAlerteChoices.APP):
        return 0

    created = sum(
        1 for admin in admins if _ensure_notification_for_admin(certificat, niveau, admin)
    )

    if created:
        _mark_alert_sent(certificat, niveau, CanalAlerteChoices.APP)
    return created


def process_certificat_alerts(certificat, admins=None, dry_run=False):
    admins = admins or list(get_admins())
    niveau = certificat.niveau_alerte_actuel()
    if not niveau or not admins:
        return {'certificat': certificat.domaine, 'niveau': None, 'email': 0, 'sms': 0, 'app': 0}

    if dry_run:
        return {
            'certificat': certificat.domaine,
            'niveau': niveau,
            'email': len(admins),
            'sms': sum(1 for admin in admins if admin.telephone),
            'app': len(admins),
            'dry_run': True,
        }

    return {
        'certificat': certificat.domaine,
        'niveau': niveau,
        'email': send_email_alert(certificat, niveau, admins),
        'sms': send_sms_alert(certificat, niveau, admins),
        'app': create_in_app_notifications(certificat, niveau, admins),
    }


def run_ssl_alert_checks(dry_run=False):
    admins = list(get_admins())
    certificats = CertificatSSL.objects.select_related('application').all()
    results = []
    stats = {'checked': 0, 'alerted': 0, 'email': 0, 'sms': 0, 'app': 0}

    for certificat in certificats:
        stats['checked'] += 1
        result = process_certificat_alerts(certificat, admins=admins, dry_run=dry_run)
        if result.get('niveau'):
            stats['alerted'] += 1
            stats['email'] += result.get('email', 0)
            stats['sms'] += result.get('sms', 0)
            stats['app'] += result.get('app', 0)
        results.append(result)

    return stats, results


def get_certificats_en_alerte():
    certificats = CertificatSSL.objects.select_related('application').all()
    alertes = []
    for certificat in certificats:
        niveau = certificat.niveau_alerte_actuel()
        if niveau:
            alertes.append({
                'certificat': certificat,
                'niveau': niveau,
                'niveau_label': NIVEAU_LABELS[niveau],
                'priorite': NIVEAU_PRIORITE[niveau],
            })
    alertes.sort(key=lambda item: (-item['priorite'], item['certificat'].date_expiration))
    return alertes
