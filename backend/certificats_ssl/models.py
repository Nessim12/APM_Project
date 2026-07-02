import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from applications.models import Application


class CertificatSSL(models.Model):
    """Certificat SSL associé à une application du patrimoine."""

    JOURS_ALERTE_RENOUVELLEMENT = 30
    JOURS_ALERTE_ANTICIPEE = 60

    class TypeChoices(models.TextChoices):
        DV = 'DV', _('Domain Validation (DV)')
        OV = 'OV', _('Organization Validation (OV)')
        EV = 'EV', _('Extended Validation (EV)')

    class StatutChoices(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif')
        EXPIRE = 'EXPIRE', _('Expiré')
        A_RENOUVELER = 'A_RENOUVELER', _('À renouveler')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='certificat_ssl',
        verbose_name=_('Application'),
    )
    domaine = models.CharField(max_length=255, verbose_name=_('Domaine / FQDN'))
    emetteur = models.CharField(max_length=255, verbose_name=_('Fournisseur SSL'))
    type_certificat = models.CharField(
        max_length=5,
        choices=TypeChoices.choices,
        verbose_name=_('Type de certificat'),
    )
    algorithme = models.CharField(max_length=100, verbose_name=_('Algorithme'))
    date_emission = models.DateField(verbose_name=_("Date d'émission"))
    date_expiration = models.DateField(verbose_name=_("Date d'expiration"))
    auto_renouvellement = models.BooleanField(default=False, verbose_name=_('Renouvellement automatique'))
    statut = models.CharField(
        max_length=15,
        choices=StatutChoices.choices,
        default=StatutChoices.ACTIF,
        verbose_name=_('État du certificat'),
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Certificat SSL')
        verbose_name_plural = _('Certificats SSL')
        ordering = ['date_expiration']

    def __str__(self):
        return f'{self.domaine} ({self.application.nom})'

    @property
    def jours_restants(self):
        return (self.date_expiration - timezone.localdate()).days

    @property
    def jours_restants_label(self):
        jours = self.jours_restants
        if jours < 0:
            return f'Expiré depuis {abs(jours)} j'
        if jours == 0:
            return "Expire aujourd'hui"
        return f'{jours} j'

    @property
    def jours_restants_css_class(self):
        jours = self.jours_restants
        if jours < 0 or jours == 0:
            return 'danger'
        if jours <= self.JOURS_ALERTE_RENOUVELLEMENT:
            return 'warning'
        return 'success'

    def _compute_statut(self):
        jours = self.jours_restants
        if jours < 0:
            return self.StatutChoices.EXPIRE
        if jours <= self.JOURS_ALERTE_RENOUVELLEMENT:
            return self.StatutChoices.A_RENOUVELER
        return self.StatutChoices.ACTIF

    @property
    def statut_calcule(self):
        return self._compute_statut()

    def get_statut_calcule_display(self):
        return self.StatutChoices(self.statut_calcule).label

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = CertificatSSL.objects.filter(pk=self.pk).only('date_expiration').first()
            if ancien and ancien.date_expiration != self.date_expiration:
                self.alertes_envoyees.all().delete()
                NotificationAdmin.objects.filter(certificat=self).delete()
        self.statut = self._compute_statut()
        super().save(*args, **kwargs)

    def niveau_alerte_actuel(self):
        jours = self.jours_restants
        if jours < 0:
            return NiveauAlerteChoices.EXPIRE
        if jours <= self.JOURS_ALERTE_RENOUVELLEMENT:
            return NiveauAlerteChoices.J30
        if jours <= self.JOURS_ALERTE_ANTICIPEE:
            return NiveauAlerteChoices.J60
        return None

    @property
    def renouvellement_label(self):
        return 'Oui (automatique)' if self.auto_renouvellement else 'Non (manuel)'


class NiveauAlerteChoices(models.TextChoices):
    J60 = 'J60', _('Expiration sous 60 jours')
    J30 = 'J30', _('Expiration sous 30 jours')
    EXPIRE = 'EXPIRE', _('Certificat expiré')


class CanalAlerteChoices(models.TextChoices):
    EMAIL = 'EMAIL', _('E-mail')
    SMS = 'SMS', _('SMS')
    APP = 'APP', _('Application')


class AlerteSSLEnvoyee(models.Model):
    """Trace les alertes déjà envoyées pour éviter les doublons."""

    certificat = models.ForeignKey(
        CertificatSSL,
        on_delete=models.CASCADE,
        related_name='alertes_envoyees',
    )
    niveau = models.CharField(max_length=10, choices=NiveauAlerteChoices.choices)
    canal = models.CharField(max_length=10, choices=CanalAlerteChoices.choices)
    envoyee_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Alerte SSL envoyée')
        verbose_name_plural = _('Alertes SSL envoyées')
        constraints = [
            models.UniqueConstraint(
                fields=['certificat', 'niveau', 'canal'],
                name='unique_alerte_ssl_par_canal',
            ),
        ]

    def __str__(self):
        return f'{self.certificat.domaine} — {self.get_niveau_display()} ({self.get_canal_display()})'


class NotificationAdmin(models.Model):
    """Notification affichée dans l'interface pour les administrateurs."""

    destinataire = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications_ssl',
    )
    certificat = models.ForeignKey(
        CertificatSSL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    niveau = models.CharField(max_length=10, choices=NiveauAlerteChoices.choices)
    titre = models.CharField(max_length=255)
    message = models.TextField()
    lue = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Notification admin SSL')
        verbose_name_plural = _('Notifications admin SSL')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.titre} → {self.destinataire.email}'
