from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from applications.models import Application
from .alerts import ensure_in_app_notifications, get_certificats_en_alerte
from .forms import CertificatSSLFilterForm, CertificatSSLForm
from .models import CertificatSSL, NotificationAdmin


def is_admin(user):
    return user.is_authenticated and user.role == User.RoleChoices.ADMIN


@login_required
@user_passes_test(is_admin)
def ssl_list(request):
    filter_form = CertificatSSLFilterForm(request.GET)
    certificats_list = CertificatSSL.objects.select_related('application').all()

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        query = data.get('q', '').strip()
        statut = data.get('statut')

        if query:
            certificats_list = certificats_list.filter(
                Q(domaine__icontains=query)
                | Q(application__nom__icontains=query)
                | Q(emetteur__icontains=query)
            )

        if statut:
            today = timezone.localdate()
            seuil_renouvellement = today + timedelta(days=CertificatSSL.JOURS_ALERTE_RENOUVELLEMENT)
            if statut == CertificatSSL.StatutChoices.EXPIRE:
                certificats_list = certificats_list.filter(date_expiration__lt=today)
            elif statut == CertificatSSL.StatutChoices.A_RENOUVELER:
                certificats_list = certificats_list.filter(
                    date_expiration__gte=today,
                    date_expiration__lte=seuil_renouvellement,
                )
            elif statut == CertificatSSL.StatutChoices.ACTIF:
                certificats_list = certificats_list.filter(date_expiration__gt=seuil_renouvellement)

    certificats_list = certificats_list.order_by('date_expiration')
    paginator = Paginator(certificats_list, 5)
    page_number = request.GET.get('page')
    certificats = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    apps_sans_certificat = Application.objects.filter(has_ssl=True).filter(
        certificat_ssl__isnull=True
    ).count()

    return render(
        request,
        'ssl/ssl_list.html',
        {
            'certificats': certificats,
            'page_obj': certificats,
            'url_params': url_params_str,
            'filter_form': filter_form,
            'has_active_filters': filter_form.is_valid() and any(
                filter_form.cleaned_data.get(field)
                for field in ('q', 'statut')
            ),
            'apps_sans_certificat': apps_sans_certificat,
            'certificats_en_alerte': get_certificats_en_alerte(),
        },
    )


@login_required
@user_passes_test(is_admin)
def ssl_detail(request, pk):
    certificat = get_object_or_404(
        CertificatSSL.objects.select_related('application'),
        pk=pk,
    )
    return render(request, 'ssl/ssl_detail.html', {'certificat': certificat})


@login_required
@user_passes_test(is_admin)
def ssl_create(request):
    application = None
    application_id = request.GET.get('application')
    if application_id:
        application = get_object_or_404(Application, pk=application_id)

    if request.method == 'POST':
        form = CertificatSSLForm(request.POST, application=application)
        if form.is_valid():
            certificat = form.save()
            ensure_in_app_notifications(certificat)
            messages.success(
                request,
                f'Certificat SSL pour « {certificat.application.nom} » enregistré avec succès.',
            )
            return redirect('ssl_detail', pk=certificat.pk)
    else:
        form = CertificatSSLForm(application=application)

    return render(
        request,
        'ssl/ssl_form.html',
        {
            'form': form,
            'action': 'Configurer',
            'application': application,
        },
    )


@login_required
@user_passes_test(is_admin)
def ssl_update(request, pk):
    certificat = get_object_or_404(CertificatSSL, pk=pk)

    if request.method == 'POST':
        form = CertificatSSLForm(
            request.POST,
            instance=certificat,
            application=certificat.application,
        )
        if form.is_valid():
            certificat = form.save()
            ensure_in_app_notifications(certificat)
            messages.success(request, f'Certificat SSL « {certificat.domaine} » mis à jour.')
            return redirect('ssl_detail', pk=certificat.pk)
    else:
        form = CertificatSSLForm(
            instance=certificat,
            application=certificat.application,
        )

    return render(
        request,
        'ssl/ssl_form.html',
        {
            'form': form,
            'action': 'Modifier',
            'certificat': certificat,
            'application': certificat.application,
        },
    )


@login_required
@user_passes_test(is_admin)
def ssl_notifications(request):
    notifications = NotificationAdmin.objects.filter(
        destinataire=request.user,
    ).select_related('certificat', 'certificat__application')

    return render(
        request,
        'ssl/ssl_notifications.html',
        {'notifications': notifications},
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def ssl_notification_mark_read(request, pk):
    notification = get_object_or_404(
        NotificationAdmin,
        pk=pk,
        destinataire=request.user,
    )
    notification.lue = True
    notification.save(update_fields=['lue'])
    messages.success(request, 'Notification marquée comme lue.')
    return redirect('ssl_notifications')


@login_required
@user_passes_test(is_admin)
@require_POST
def ssl_notifications_mark_all_read(request):
    updated = NotificationAdmin.objects.filter(
        destinataire=request.user,
        lue=False,
    ).update(lue=True)
    messages.success(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    return redirect('ssl_notifications')
