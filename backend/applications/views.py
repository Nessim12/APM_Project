from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.urls import reverse

from accounts.models import User
from .forms import ApplicationFilterForm, ApplicationForm
from .models import Application

CertificatSSL = apps.get_model('ssl', 'CertificatSSL')


def is_admin(user):
    return user.is_authenticated and user.role == User.RoleChoices.ADMIN


def _filtered_queryset(request):
    """
    Construit le queryset filtré selon les paramètres GET.
    Exclut les archivées par défaut, sauf si le filtre statut = Archivé.
    """
    filter_form = ApplicationFilterForm(request.GET)
    show_archived = (
        filter_form.is_valid()
        and filter_form.cleaned_data.get('statut') == Application.StatutChoices.ARCHIVE
    )

    if show_archived:
        queryset = Application.all_objects.archivees()
    else:
        queryset = Application.objects.all()

    if filter_form.is_valid():
        data = filter_form.cleaned_data

        if data.get('nom'):
            queryset = queryset.filter(nom__icontains=data['nom'])

        if data.get('criticite'):
            queryset = queryset.filter(criticite=data['criticite'])

        if data.get('statut') and not show_archived:
            queryset = queryset.filter(statut=data['statut'])

        if data.get('direction_metier'):
            queryset = queryset.filter(direction_metier__icontains=data['direction_metier'])

        if data.get('responsable'):
            responsable = data['responsable']
            queryset = queryset.filter(
                Q(responsable_metier=responsable)
                | Q(responsable_technique=responsable)
                | Q(chef_de_projet=responsable)
                | Q(equipe_support=responsable)
            )

    return queryset.select_related(
        'responsable_metier',
        'responsable_technique',
        'chef_de_projet',
        'equipe_support',
    ).order_by('nom'), filter_form


@login_required
@user_passes_test(is_admin)
def application_list(request):
    """Liste du patrimoine applicatif avec moteur de filtrage multicritères."""
    applications_list, filter_form = _filtered_queryset(request)
    paginator = Paginator(applications_list, 5)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    return render(
        request,
        'applications/application_list.html',
        {
            'applications': applications,
            'page_obj': applications,
            'url_params': url_params_str,
            'filter_form': filter_form,
        },
    )


@login_required
@user_passes_test(is_admin)
def application_detail(request, pk):
    """Consultation unitaire — fiche complète de l'application."""
    application = get_object_or_404(
        Application.objects.select_related(
            'responsable_metier',
            'responsable_technique',
            'chef_de_projet',
            'equipe_support',
            'certificat_ssl',
        ).prefetch_related('documents'),
        pk=pk,
    )
    return render(
        request,
        'applications/application_detail.html',
        {'application': application},
    )


@login_required
@user_passes_test(is_admin)
def application_create(request):
    """Création d'une nouvelle application."""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            if application.has_ssl:
                messages.success(
                    request,
                    f'Application « {application.nom} » créée. Configurez maintenant son certificat SSL.',
                )
                return redirect(f"{reverse('ssl_create')}?application={application.pk}")
            messages.success(request, f'Application « {application.nom} » créée avec succès.')
            return redirect('application_detail', pk=application.pk)
    else:
        form = ApplicationForm()

    return render(
        request,
        'applications/application_form.html',
        {'form': form, 'action': 'Créer'},
    )


@login_required
@user_passes_test(is_admin)
def application_update(request, pk):
    """Modification des métadonnées et des responsables assignés."""
    application = get_object_or_404(Application, pk=pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            had_ssl = application.has_ssl
            application = form.save()
            if application.has_ssl and not had_ssl and not CertificatSSL.objects.filter(application=application).exists():
                messages.success(
                    request,
                    f'Application « {application.nom} » mise à jour. Configurez son certificat SSL.',
                )
                return redirect(f"{reverse('ssl_create')}?application={application.pk}")
            messages.success(request, f'Application « {application.nom} » mise à jour.')
            return redirect('application_detail', pk=application.pk)
    else:
        form = ApplicationForm(instance=application)

    return render(
        request,
        'applications/application_form.html',
        {'form': form, 'action': 'Modifier', 'application': application},
    )


@login_required
@user_passes_test(is_admin)
def application_archive(request, pk):
    """
    Archivage logique (soft delete).
    Aucune suppression physique — le statut passe à « Archivé ».
    """
    application = get_object_or_404(Application, pk=pk)

    if request.method == 'POST':
        nom = application.nom
        application.delete()
        messages.success(request, f'Application « {nom} » archivée avec succès.')
        return redirect('application_list')

    return redirect('application_detail', pk=pk)
