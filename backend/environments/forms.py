from django import forms
from django.core.exceptions import ValidationError

from .models import Environnement, Server


class EnvironnementForm(forms.ModelForm):
    class Meta:
        model = Environnement
        fields = [
            'nom',
            'url',
            'adresse_ip',
            'os',
            'cpu',
            'ram',
            'hebergeur',
            'type_hebergement',
            'docker',
            'kubernetes',
            'application',
            'serveur',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom de l’environnement'}),
            'url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...' }),
            'adresse_ip': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Adresse IP'}),
            'os': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Linux, Windows...'}),
            'cpu': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: 4 vCPU'}),
            'ram': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: 16GB'}),
            'hebergeur': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Fournisseur d’hébergement'}),
            'type_hebergement': forms.Select(attrs={'class': 'form-select'}),
            'docker': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'kubernetes': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'application': forms.Select(attrs={'class': 'form-select'}),
            'serveur': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['serveur'].queryset = Server.objects.all()
        self.fields['serveur'].empty_label = '— Aucun serveur disponible —'
        self.fields['application'].empty_label = '— Sélectionner une application —'

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if not nom:
            raise ValidationError('Le nom de l’environnement est obligatoire.')
        return nom

    def clean_hebergeur(self):
        hebergeur = self.cleaned_data.get('hebergeur', '').strip()
        if not hebergeur:
            raise ValidationError('Le nom de l’hébergeur est obligatoire.')
        return hebergeur

    def clean_os(self):
        os_value = self.cleaned_data.get('os', '').strip()
        if not os_value:
            raise ValidationError('Le système d’exploitation est obligatoire.')
        return os_value

    def clean_cpu(self):
        cpu = self.cleaned_data.get('cpu', '').strip()
        if not cpu:
            raise ValidationError('Le détail CPU est obligatoire.')
        return cpu

    def clean_ram(self):
        ram = self.cleaned_data.get('ram', '').strip()
        if not ram:
            raise ValidationError('La mémoire RAM est obligatoire.')
        return ram

    def clean(self):
        cleaned_data = super().clean()
        nom = cleaned_data.get('nom')
        application = cleaned_data.get('application')

        if nom and application:
            qs = Environnement.objects.filter(nom__iexact=nom, application=application)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Un environnement avec ce nom existe déjà pour cette application.')

        return cleaned_data


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ['hostname', 'adresse_ip', 'systeme_exploitation', 'description']
        widgets = {
            'hostname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom du serveur'}),
            'adresse_ip': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Adresse IP'}),
            'systeme_exploitation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Linux, Windows...'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Informations supplémentaires'}),
        }

    def clean_hostname(self):
        hostname = self.cleaned_data.get('hostname', '').strip()
        if not hostname:
            raise ValidationError('Le nom du serveur est obligatoire.')
        return hostname

    def clean(self):
        cleaned_data = super().clean()
        hostname = cleaned_data.get('hostname')
        if hostname:
            qs = Server.objects.filter(hostname__iexact=hostname)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Un serveur avec ce nom existe déjà.')
        return cleaned_data
