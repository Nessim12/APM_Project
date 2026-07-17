from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from .forms import DomaineForm
from .models import Domaine


def is_admin(user):
    return user.is_authenticated and user.role != 'TECH'


@login_required
def domaine_list(request):
    query = request.GET.get('q', '').strip()
    domaines_list = Domaine.objects.all()
    if query:
        domaines_list = domaines_list.filter(nom__icontains=query)
        
    domaines_list = domaines_list.order_by('nom')
    paginator = Paginator(domaines_list, 5)
    page_number = request.GET.get('page')
    domaines = paginator.get_page(page_number)
    
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    return render(
        request,
        'domaines/domaine_list.html',
        {
            'domaines': domaines,
            'page_obj': domaines,
            'url_params': url_params_str,
            'query': query,
        },
    )


@login_required
def domaine_detail(request, pk):
    domaine = get_object_or_404(Domaine, pk=pk)
    return render(request, 'domaines/domaine_detail.html', {'domaine': domaine})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def domaine_create(request):
    if request.method == 'POST':
        form = DomaineForm(request.POST)
        if form.is_valid():
            domaine = form.save()
            messages.success(request, f'Domaine « {domaine.nom} » créé avec succès.')
            return redirect('domaine_detail', pk=domaine.pk)
    else:
        form = DomaineForm()

    return render(request, 'domaines/domaine_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def domaine_update(request, pk):
    domaine = get_object_or_404(Domaine, pk=pk)
    if request.method == 'POST':
        form = DomaineForm(request.POST, instance=domaine)
        if form.is_valid():
            form.save()
            messages.success(request, f'Domaine « {domaine.nom} » mis à jour.')
            return redirect('domaine_detail', pk=domaine.pk)
    else:
        form = DomaineForm(instance=domaine)

    return render(request, 'domaines/domaine_form.html', {'form': form, 'action': 'Modifier', 'domaine': domaine})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def domaine_delete(request, pk):
    domaine = get_object_or_404(Domaine, pk=pk)
    if request.method == 'POST':
        domaine.delete()
        messages.success(request, f'Domaine « {domaine.nom} » supprimé.')
        return redirect('domaine_list')
    return render(request, 'domaines/domaine_confirm_delete.html', {'domaine': domaine})
