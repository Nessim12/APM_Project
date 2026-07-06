import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Domaine


DOMAIN_NAME_RE = re.compile(
    r'^(?=.{1,253}$)(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}$',
    re.IGNORECASE,
)
DNS_ENTRY_RE = re.compile(
    r'^(?:(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}|\d{1,3}(?:\.\d{1,3}){3})$',
    re.IGNORECASE,
)


class DomaineForm(forms.ModelForm):
    class Meta:
        model = Domaine
        fields = [
            'nom',
            'registrar',
            'dns',
            'responsable',
            'date_achat',
            'date_expiration',
            'renouvellement_auto',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'exemple.com'}),
            'registrar': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Registrar'}),
            'dns': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ns1.exemple.com, ns2.exemple.com'}),
            'responsable': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom du responsable'}),
            'date_achat': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_expiration': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'renouvellement_auto': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip().lower()
        if not nom:
            raise ValidationError('Le nom de domaine est obligatoire.')
        if not DOMAIN_NAME_RE.match(nom):
            raise ValidationError('Le nom de domaine est invalide. Ex: exemple.com')
        qs = Domaine.objects.filter(nom=nom)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ce domaine existe déjà.')
        return nom

    def clean_registrar(self):
        registrar = self.cleaned_data.get('registrar', '').strip()
        if not registrar:
            raise ValidationError('Le registrar est obligatoire.')
        if len(registrar) < 2:
            raise ValidationError('Le registrar est trop court.')
        return registrar

    def clean_dns(self):
        dns = self.cleaned_data.get('dns', '').strip()
        if not dns:
            raise ValidationError('Le DNS est obligatoire.')

        entries = [entry.strip() for entry in dns.split(',') if entry.strip()]
        if not entries:
            raise ValidationError('Le DNS doit contenir au moins une entrée.')

        invalid = [entry for entry in entries if not DNS_ENTRY_RE.match(entry)]
        if invalid:
            raise ValidationError(
                'Entrée DNS invalide : %s. Utilisez des hôtes ou des adresses IP valides séparés par des virgules.'
                % ', '.join(invalid)
            )
        return ', '.join(entries)

    def clean_responsable(self):
        responsable = self.cleaned_data.get('responsable', '').strip()
        if not responsable:
            raise ValidationError('Le responsable est obligatoire.')
        if len(responsable) < 2:
            raise ValidationError('Le nom du responsable est trop court.')
        return responsable

    def clean(self):
        cleaned_data = super().clean()
        date_achat = cleaned_data.get('date_achat')
        date_expiration = cleaned_data.get('date_expiration')

        if date_achat and date_expiration and date_expiration <= date_achat:
            raise ValidationError('La date d’expiration doit être postérieure à la date d’achat.')

        return cleaned_data
