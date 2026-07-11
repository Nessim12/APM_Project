import os

from django import forms
from django.core.exceptions import ValidationError

from applications.models import Application
from certificats_ssl.models import CertificatSSL
from domaines.models import Domaine
from environments.models import Environnement

from .models import ALLOWED_EXTENSIONS, Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'nom',
            'categorie',
            'description',
            'type_gestion',
            'application',
            'environnement',
            'certificat_ssl',
            'domaine',
            'fichier',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom du document'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Description optionnelle…'}),
            'type_gestion': forms.Select(attrs={'class': 'form-select', 'id': 'id_type_gestion'}),
            'application': forms.Select(attrs={'class': 'form-select doc-relation-field', 'data-relation': 'APPLICATION'}),
            'environnement': forms.Select(attrs={'class': 'form-select doc-relation-field', 'data-relation': 'ENVIRONNEMENT'}),
            'certificat_ssl': forms.Select(attrs={'class': 'form-select doc-relation-field', 'data-relation': 'SSL'}),
            'domaine': forms.Select(attrs={'class': 'form-select doc-relation-field', 'data-relation': 'DOMAINE'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'file-input', 'accept': ','.join(ALLOWED_EXTENSIONS)}),
        }

    def __init__(self, *args, **kwargs):
        self.initial_type_gestion = kwargs.pop('initial_type_gestion', None)
        self.initial_application = kwargs.pop('initial_application', None)
        self.initial_environnement = kwargs.pop('initial_environnement', None)
        self.initial_certificat_ssl = kwargs.pop('initial_certificat_ssl', None)
        self.initial_domaine = kwargs.pop('initial_domaine', None)
        super().__init__(*args, **kwargs)

        self.fields['application'].queryset = Application.objects.order_by('nom')
        self.fields['environnement'].queryset = Environnement.objects.select_related('application').order_by('nom')
        self.fields['certificat_ssl'].queryset = CertificatSSL.objects.select_related('application').order_by('domaine')
        self.fields['domaine'].queryset = Domaine.objects.order_by('nom')

        for field_name in ('application', 'environnement', 'certificat_ssl', 'domaine'):
            self.fields[field_name].required = False

        if not self.instance.pk:
            self.fields['fichier'].required = True
            if self.initial_type_gestion:
                self.fields['type_gestion'].initial = self.initial_type_gestion
            if self.initial_application:
                self.fields['application'].initial = self.initial_application
            if self.initial_environnement:
                self.fields['environnement'].initial = self.initial_environnement
            if self.initial_certificat_ssl:
                self.fields['certificat_ssl'].initial = self.initial_certificat_ssl
            if self.initial_domaine:
                self.fields['domaine'].initial = self.initial_domaine

    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if not fichier:
            if self.instance.pk and self.instance.fichier:
                return self.instance.fichier
            raise ValidationError('Le fichier est obligatoire.')

        ext = os.path.splitext(fichier.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'Type de fichier non autorisé ({ext}). '
                f'Formats acceptés : {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            )

        if fichier.size > 50 * 1024 * 1024:
            raise ValidationError('Le fichier ne doit pas dépasser 50 Mo.')

        return fichier

    def clean(self):
        cleaned_data = super().clean()
        type_gestion = cleaned_data.get('type_gestion')
        application = cleaned_data.get('application')
        environnement = cleaned_data.get('environnement')
        certificat_ssl = cleaned_data.get('certificat_ssl')
        domaine = cleaned_data.get('domaine')

        relation_map = {
            Document.TypeGestion.APPLICATION: ('application', application, 'une application'),
            Document.TypeGestion.ENVIRONNEMENT: ('environnement', environnement, 'un environnement'),
            Document.TypeGestion.SSL: ('certificat_ssl', certificat_ssl, 'un certificat SSL'),
            Document.TypeGestion.DOMAINE: ('domaine', domaine, 'un domaine'),
        }

        for gestion_type, (field_name, value, label) in relation_map.items():
            if type_gestion == gestion_type and not value:
                self.add_error(field_name, f'Veuillez sélectionner {label}.')

        if type_gestion == Document.TypeGestion.GENERAL:
            cleaned_data['application'] = None
            cleaned_data['environnement'] = None
            cleaned_data['certificat_ssl'] = None
            cleaned_data['domaine'] = None
        elif type_gestion == Document.TypeGestion.APPLICATION:
            cleaned_data['environnement'] = None
            cleaned_data['certificat_ssl'] = None
            cleaned_data['domaine'] = None
        elif type_gestion == Document.TypeGestion.ENVIRONNEMENT:
            cleaned_data['application'] = None
            cleaned_data['certificat_ssl'] = None
            cleaned_data['domaine'] = None
        elif type_gestion == Document.TypeGestion.SSL:
            cleaned_data['application'] = None
            cleaned_data['environnement'] = None
            cleaned_data['domaine'] = None
        elif type_gestion == Document.TypeGestion.DOMAINE:
            cleaned_data['application'] = None
            cleaned_data['environnement'] = None
            cleaned_data['certificat_ssl'] = None

        return cleaned_data


class DocumentFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Rechercher par nom…',
    }))
    categorie = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les catégories')] + list(Document.Categorie.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    type_gestion = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les modules')] + list(Document.TypeGestion.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    type_fichier = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Type (pdf, png…)',
    }))
