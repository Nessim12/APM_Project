import mimetypes
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DocumentFilterForm, DocumentForm
from .models import Document


def is_admin(user):
    return user.is_authenticated and user.role != 'TECH'


def _filtered_queryset(request):
    filter_form = DocumentFilterForm(request.GET)
    queryset = Document.objects.select_related(
        'application',
        'environnement',
        'certificat_ssl',
        'domaine',
        'uploaded_by',
    )

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get('q'):
            queryset = queryset.filter(
                Q(nom__icontains=data['q']) | Q(description__icontains=data['q'])
            )
        if data.get('categorie'):
            queryset = queryset.filter(categorie=data['categorie'])
        if data.get('type_gestion'):
            queryset = queryset.filter(type_gestion=data['type_gestion'])
        if data.get('type_fichier'):
            queryset = queryset.filter(type_fichier__icontains=data['type_fichier'].strip('.'))

    return queryset, filter_form


@login_required
def document_list(request):
    queryset, filter_form = _filtered_queryset(request)
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    documents = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f'&{url_params}' if url_params else ''

    return render(request, 'documentation/document_list.html', {
        'documents': documents,
        'page_obj': documents,
        'filter_form': filter_form,
        'url_params': url_params_str,
    })


@login_required
def document_detail(request, pk):
    document = get_object_or_404(
        Document.objects.select_related(
            'application', 'environnement', 'certificat_ssl', 'domaine', 'uploaded_by',
        ),
        pk=pk,
    )
    return render(request, 'documentation/document_detail.html', {'document': document})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def document_create(request):
    initial_kwargs = {}
    if request.GET.get('type_gestion'):
        initial_kwargs['initial_type_gestion'] = request.GET['type_gestion']
    if request.GET.get('application'):
        initial_kwargs['initial_application'] = request.GET['application']
    if request.GET.get('environnement'):
        initial_kwargs['initial_environnement'] = request.GET['environnement']
    if request.GET.get('certificat_ssl'):
        initial_kwargs['initial_certificat_ssl'] = request.GET['certificat_ssl']
    if request.GET.get('domaine'):
        initial_kwargs['initial_domaine'] = request.GET['domaine']

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'Document « {document.nom} » ajouté avec succès.')
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(**initial_kwargs)

    return render(request, 'documentation/document_form.html', {
        'form': form,
        'action': 'Ajouter',
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def document_update(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, f'Document « {document.nom} » mis à jour.')
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(instance=document)

    return render(request, 'documentation/document_form.html', {
        'form': form,
        'action': 'Modifier',
        'document': document,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        nom = document.nom
        if document.fichier:
            document.fichier.delete(save=False)
        document.delete()
        messages.success(request, f'Document « {nom} » supprimé.')
        return redirect('document_list')
    return render(request, 'documentation/document_confirm_delete.html', {'document': document})


@login_required
def document_preview(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not document.fichier:
        raise Http404('Fichier introuvable.')

    content_type, _ = mimetypes.guess_type(document.fichier.name)
    filename = os.path.basename(document.fichier.name)
    display_name = f'{document.nom}{os.path.splitext(filename)[1]}'

    response = FileResponse(document.fichier.open('rb'), content_type=content_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{display_name}"'
    return response


@login_required
def document_download(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not document.fichier:
        raise Http404('Fichier introuvable.')

    content_type, _ = mimetypes.guess_type(document.fichier.name)
    filename = os.path.basename(document.fichier.name)
    display_name = f'{document.nom}{os.path.splitext(filename)[1]}'

    response = FileResponse(document.fichier.open('rb'), content_type=content_type or 'application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{display_name}"'
    return response
