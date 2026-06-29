from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DomaineForm
from .models import Domaine


def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


@login_required
@user_passes_test(is_admin)
def domaine_list(request):
    query = request.GET.get('q', '').strip()
    domaines = Domaine.objects.all()
    if query:
        domaines = domaines.filter(nom__icontains=query)

    return render(
        request,
        'domaines/domaine_list.html',
        {
            'domaines': domaines.order_by('nom'),
            'query': query,
        },
    )


@login_required
@user_passes_test(is_admin)
def domaine_detail(request, pk):
    domaine = get_object_or_404(Domaine, pk=pk)
    return render(request, 'domaines/domaine_detail.html', {'domaine': domaine})


@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def domaine_delete(request, pk):
    domaine = get_object_or_404(Domaine, pk=pk)
    if request.method == 'POST':
        domaine.delete()
        messages.success(request, f'Domaine « {domaine.nom} » supprimé.')
        return redirect('domaine_list')
    return render(request, 'domaines/domaine_confirm_delete.html', {'domaine': domaine})
