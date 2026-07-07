from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EnvironnementForm, ServerForm
from .models import Environnement, Server


def is_admin(user):
    return user.is_authenticated and user.role != 'TECH'


@login_required
def environment_list(request):
    query = request.GET.get('q', '').strip()
    environments = Environnement.objects.select_related('application', 'serveur')
    if query:
        environments = environments.filter(nom__icontains=query)

    return render(
        request,
        'environments/environment_list.html',
        {
            'environments': environments.order_by('nom'),
            'query': query,
        },
    )


@login_required
def environment_detail(request, pk):
    environment = get_object_or_404(Environnement.objects.select_related('application', 'serveur'), pk=pk)
    return render(request, 'environments/environment_detail.html', {'environment': environment})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def environment_create(request):
    if request.method == 'POST':
        form = EnvironnementForm(request.POST)
        if form.is_valid():
            environment = form.save()
            messages.success(request, f'Environnement « {environment.nom} » créé avec succès.')
            return redirect('environment_detail', pk=environment.pk)
    else:
        form = EnvironnementForm()

    return render(request, 'environments/environment_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def environment_update(request, pk):
    environment = get_object_or_404(Environnement, pk=pk)
    if request.method == 'POST':
        form = EnvironnementForm(request.POST, instance=environment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Environnement « {environment.nom} » mis à jour.')
            return redirect('environment_detail', pk=environment.pk)
    else:
        form = EnvironnementForm(instance=environment)

    return render(request, 'environments/environment_form.html', {'form': form, 'action': 'Modifier', 'environment': environment})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def environment_delete(request, pk):
    environment = get_object_or_404(Environnement, pk=pk)
    if request.method == 'POST':
        environment.delete()
        messages.success(request, f'Environnement « {environment.nom} » supprimé.')
        return redirect('environment_list')
    return render(request, 'environments/environment_confirm_delete.html', {'environment': environment})


def server_list(request):
    query = request.GET.get('q', '').strip()
    servers = Server.objects.all()
    if query:
        servers = servers.filter(hostname__icontains=query)

    return render(
        request,
        'environments/server_list.html',
        {
            'servers': servers.order_by('hostname'),
            'query': query,
        },
    )


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def server_create(request):
    if request.method == 'POST':
        form = ServerForm(request.POST)
        if form.is_valid():
            server = form.save()
            messages.success(request, f'Serveur « {server.hostname} » créé avec succès.')
            return redirect('server_list')
    else:
        form = ServerForm()

    return render(request, 'environments/server_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def server_update(request, pk):
    server = get_object_or_404(Server, pk=pk)
    if request.method == 'POST':
        form = ServerForm(request.POST, instance=server)
        if form.is_valid():
            form.save()
            messages.success(request, f'Serveur « {server.hostname} » mis à jour.')
            return redirect('server_list')
    else:
        form = ServerForm(instance=server)

    return render(request, 'environments/server_form.html', {'form': form, 'action': 'Modifier', 'server': server})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def server_delete(request, pk):
    server = get_object_or_404(Server, pk=pk)
    if request.method == 'POST':
        server.delete()
        messages.success(request, f'Serveur « {server.hostname} » supprimé.')
        return redirect('server_list')
    return render(request, 'environments/server_confirm_delete.html', {'server': server})
