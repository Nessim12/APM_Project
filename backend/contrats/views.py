from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse

from .forms import ContractFilterForm, ContractForm, FournisseurForm
from .models import Contract, Fournisseur


def is_admin(user):
    return user.is_authenticated and user.role != 'TECH'


# ── Dashboard principal (4 cartes par type) ───────────────────────────────────

@login_required
def contract_dashboard(request):
    """Affiche 4 cartes (une par type) avec stats globales."""

    # Aggregation en une seule requête GROUP BY (exclut les archivés)
    counts_qs = (
        Contract.objects.filter(archived=False).values('contract_type')
        .annotate(total=Count('id'))
    )
    counts = {row['contract_type']: row['total'] for row in counts_qs}

    # Stats par statut (toutes types confondus)
    statut_qs = (
        Contract.objects.filter(archived=False).values('statut')
        .annotate(total=Count('id'))
    )
    statut_counts = {row['statut']: row['total'] for row in statut_qs}

    # Coût total annuel
    total_cout = Contract.objects.filter(archived=False).aggregate(total=Sum('cout_annuel'))['total'] or 0

    # Contrats proches expiration (≤ 90 jours, non expirés)
    from datetime import date, timedelta
    today = date.today()
    bientot_expires = Contract.objects.filter(
        archived=False,
        date_fin__gte=today,
        date_fin__lte=today + timedelta(days=90),
    ).count()

    types = [
        {
            'key': 'MAINTENANCE',
            'label': 'Maintenance',
            'count': counts.get('MAINTENANCE', 0),
            'icon': '🔧',
            'color': '#3b82f6',
            'bg': 'rgba(59,130,246,0.12)',
            'description': 'Contrats de maintenance corrective et préventive.',
        },
        {
            'key': 'SUPPORT',
            'label': 'Support',
            'count': counts.get('SUPPORT', 0),
            'icon': '🎧',
            'color': '#8b5cf6',
            'bg': 'rgba(139,92,246,0.12)',
            'description': 'Contrats de support technique et assistance utilisateurs.',
        },
        {
            'key': 'GARANTIE',
            'label': 'Garantie',
            'count': counts.get('GARANTIE', 0),
            'icon': '🛡️',
            'color': '#10b981',
            'bg': 'rgba(16,185,129,0.12)',
            'description': 'Contrats de garantie éditeur ou matérielle.',
        },
        {
            'key': 'RENOUVELLEMENT',
            'label': 'Renouvellement',
            'count': counts.get('RENOUVELLEMENT', 0),
            'icon': '🔄',
            'color': '#f59e0b',
            'bg': 'rgba(245,158,11,0.12)',
            'description': 'Contrats de renouvellement de licences ou abonnements.',
        },
    ]

    total_contrats = sum(t['count'] for t in types)

    return render(request, 'contrats/contract_dashboard.html', {
        'types': types,
        'total_contrats': total_contrats,
        'total_cout': total_cout,
        'statut_counts': statut_counts,
        'bientot_expires': bientot_expires,
    })


# ── Liste par type ─────────────────────────────────────────────────────────────

def _get_filtered_contracts(request, contract_type):
    queryset = (
        Contract.objects
        .filter(contract_type=contract_type, archived=False)
        .select_related('application', 'fournisseur')
    )
    filter_form = ContractFilterForm(request.GET)
    queryset = filter_form.filter_queryset(queryset)
    return queryset, filter_form


@login_required
def contract_type_list(request, contract_type):
    contract_type = contract_type.upper()
    if contract_type not in Contract.ContractTypeChoices.values:
        return redirect('contrats:contrat_dashboard')

    contracts, filter_form = _get_filtered_contracts(request, contract_type)

    # Stats rapides pour la barre de résumé
    from datetime import date, timedelta
    today = date.today()
    stats = {
        'total': contracts.count(),
        'actifs': contracts.filter(statut=Contract.StatutChoices.ACTIF).count(),
        'expires': contracts.filter(statut=Contract.StatutChoices.EXPIRE).count(),
        'bientot': contracts.filter(
            date_fin__gte=today,
            date_fin__lte=today + timedelta(days=90),
        ).count(),
    }

    paginator = Paginator(contracts, 8)
    page_number = request.GET.get('page')
    contracts_page = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    # Métadonnées du type courant
    type_meta = Contract.TYPE_META.get(contract_type, {
        'icon': '📄', 'color': '#6b7280', 'bg': 'rgba(107,114,128,0.12)',
    })

    return render(request, 'contrats/contract_list.html', {
        'contracts': contracts_page,
        'page_obj': contracts_page,
        'url_params': url_params_str,
        'filter_form': filter_form,
        'contract_type': contract_type,
        'contract_type_label': Contract.ContractTypeChoices(contract_type).label,
        'type_meta': type_meta,
        'stats': stats,
    })


# ── Détail ────────────────────────────────────────────────────────────────────

@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related('application', 'fournisseur').filter(archived=False),
        pk=pk,
    )
    return render(request, 'contrats/contract_detail.html', {'contract': contract})


# ── Création ──────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin, login_url='dashboard')
def contract_create(request):
    selected_type = request.GET.get('type', '').upper()
    if selected_type not in Contract.ContractTypeChoices.values:
        selected_type = ''

    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save()
            messages.success(request, f'Contrat « {contract.numero_contrat} » créé avec succès.')
            return redirect('contrats:contract_detail', pk=contract.pk)
    else:
        initial = {'contract_type': selected_type} if selected_type else {}
        form = ContractForm(initial=initial)

    return render(request, 'contrats/contract_form.html', {
        'form': form,
        'action': 'Créer',
        'selected_type': selected_type,
    })


# ── Modification ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin, login_url='dashboard')
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            contract = form.save()
            messages.success(request, f'Contrat « {contract.numero_contrat} » mis à jour.')
            return redirect('contrats:contract_detail', pk=contract.pk)
    else:
        form = ContractForm(instance=contract)

    return render(request, 'contrats/contract_form.html', {
        'form': form,
        'action': 'Modifier',
        'contract': contract,
    })


# ── Suppression ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin, login_url='dashboard')
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        # Soft-delete: archive the contract so it can be restored later
        numero = contract.numero_contrat
        contract_type = contract.contract_type
        contract.archive()
        actor = request.user.get_full_name() or request.user.username
        label = Contract.ContractTypeChoices(contract_type).label
        ts = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        undo_url = reverse('contrats:undo_contract', args=[contract.pk])
        undo_button = f' <button class="btn-undo" data-undo-url="{undo_url}">Annuler</button>'
        message_html = f'Contrat « {numero} » ({label}) supprimé par {actor} le {ts}.{undo_button}'
        messages.success(request, mark_safe(message_html))
        return redirect('contrats:contrat_type_list', contract_type=contract_type)
    # GET request — should not happen, redirect to detail
    return redirect('contrats:contract_detail', pk=pk)


# ── Fournisseurs ──────────────────────────────────────────────────────────────

@login_required
def fournisseur_list(request):
    query = request.GET.get('q', '')
    fournisseurs_all = Fournisseur.objects.filter(archived=False).annotate(
        nb_contrats=Count('contrats', filter=Q(contrats__archived=False))
    ).order_by('nom')
    
    # Statistiques globales
    total_fournisseurs = fournisseurs_all.count()
    fournisseurs_actifs = fournisseurs_all.filter(nb_contrats__gt=0).count()
    
    # Nombre total de contrats actifs
    total_contrats_fournisseurs = Contract.objects.filter(archived=False).count()
    
    # Coût total des contrats et coût moyen par fournisseur
    cout_stats = Contract.objects.filter(archived=False).aggregate(
        total=Sum('cout_annuel')
    )
    cout_total = cout_stats['total'] or 0
    cout_total_fournisseurs = cout_total / total_fournisseurs if total_fournisseurs > 0 else 0
    
    # Top 5 fournisseurs les plus utilisés
    top_fournisseurs = fournisseurs_all.order_by('-nb_contrats')[:5]
    max_contrats = top_fournisseurs.first().nb_contrats if top_fournisseurs.exists() else 1
    
    # Filtrages
    fournisseurs = fournisseurs_all
    if query:
        fournisseurs = fournisseurs.filter(
            Q(nom__icontains=query)
            | Q(email__icontains=query)
            | Q(telephone__icontains=query)
            | Q(adresse__icontains=query)
            | Q(responsable__icontains=query)
        )

    paginator = Paginator(fournisseurs, 8)
    page_number = request.GET.get('page')
    fournisseurs_page = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    return render(request, 'contrats/fournisseur_list.html', {
        'fournisseurs': fournisseurs_page,
        'page_obj': fournisseurs_page,
        'url_params': url_params_str,
        'query': query,
        'total_fournisseurs': total_fournisseurs,
        'fournisseurs_actifs': fournisseurs_actifs,
        'total_contrats_fournisseurs': total_contrats_fournisseurs,
        'cout_total_fournisseurs': cout_total_fournisseurs,
        'top_fournisseurs': top_fournisseurs,
        'max_contrats': max_contrats,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def fournisseur_create(request):
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            fournisseur = form.save()
            messages.success(request, f'Fournisseur « {fournisseur.nom} » créé avec succès.')
            return redirect('contrats:fournisseur_list')
    else:
        form = FournisseurForm()

    return render(request, 'contrats/fournisseur_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def fournisseur_update(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            fournisseur = form.save()
            messages.success(request, f'Fournisseur « {fournisseur.nom} » mis à jour.')
            return redirect('contrats:fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)

    return render(request, 'contrats/fournisseur_form.html', {
        'form': form,
        'action': 'Modifier',
        'fournisseur': fournisseur,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def fournisseur_delete(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        nom = fournisseur.nom
        related_count = fournisseur.contrats.filter(archived=False).count()
        if related_count > 0:
            messages.error(
                request,
                f"Impossible de supprimer le fournisseur « {nom} » : {related_count} contrat(s) y sont attachés."
            )
            return redirect('contrats:fournisseur_list')
        # Soft-delete
        fournisseur.archived = True
        fournisseur.save()
        actor = request.user.get_full_name() or request.user.username
        ts = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        undo_url = reverse('contrats:undo_fournisseur', args=[fournisseur.pk])
        undo_button = f' <button class="btn-undo" data-undo-url="{undo_url}">Annuler</button>'
        message_html = f'Fournisseur « {nom} » supprimé par {actor} le {ts}.{undo_button}'
        messages.success(request, mark_safe(message_html))
        return redirect('contrats:fournisseur_list')
    # GET request — should not happen, redirect to list
    return redirect('contrats:fournisseur_list')


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def undo_fournisseur(request, pk):
    if request.method != 'POST':
        return redirect('contrats:fournisseur_list')
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    fournisseur.archived = False
    fournisseur.save()
    messages.success(request, f'Annulation : fournisseur « {fournisseur.nom} » restauré.')
    return redirect('contrats:fournisseur_list')


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def undo_contract(request, pk):
    if request.method != 'POST':
        return redirect('contrats:contrat_dashboard')
    contract = get_object_or_404(Contract.all_objects, pk=pk)
    contract.restore()
    messages.success(request, f'Annulation : contrat « {contract.numero_contrat} » restauré.')
    return redirect('contrats:contrat_type_list', contract_type=contract.contract_type)


@login_required
def fournisseur_detail(request, pk):
    fournisseur = get_object_or_404(
        Fournisseur.objects.filter(archived=False),
        pk=pk
    )
    # Fetch all active contracts associated with this provider
    contrats = fournisseur.contrats.filter(archived=False).select_related('application')
    
    # Calculate quick stats for this provider
    total_contrats = contrats.count()
    cout_total = contrats.aggregate(total=Sum('cout_annuel'))['total'] or 0
    contrats_actifs = contrats.filter(statut=Contract.StatutChoices.ACTIF).count()
    contrats_expires = contrats.filter(statut=Contract.StatutChoices.EXPIRE).count()
    
    return render(request, 'contrats/fournisseur_detail.html', {
        'fournisseur': fournisseur,
        'contrats': contrats,
        'total_contrats': total_contrats,
        'cout_total': cout_total,
        'contrats_actifs': contrats_actifs,
        'contrats_expires': contrats_expires,
    })
