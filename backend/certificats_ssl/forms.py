import re

from django import forms
from django.core.exceptions import ValidationError

from applications.models import Application
from .models import CertificatSSL


class CertificatSSLFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Recherche',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Domaine, application ou fournisseur…',
        }),
    )
    statut = forms.ChoiceField(
        required=False,
        label='État',
        choices=[('', '— Tous —')] + list(CertificatSSL.StatutChoices.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


DOMAIN_NAME_RE = re.compile(
    r'^(?=.{1,253}$)(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}$',
    re.IGNORECASE,
)


def _applications_avec_ssl():
    return Application.objects.filter(has_ssl=True).order_by('nom')


class CertificatSSLForm(forms.ModelForm):
    class Meta:
        model = CertificatSSL
        fields = [
            'application',
            'domaine',
            'emetteur',
            'type_certificat',
            'algorithme',
            'date_emission',
            'date_expiration',
            'auto_renouvellement',
            'notes',
        ]
        labels = {
            'emetteur': 'Fournisseur SSL',
        }
        widgets = {
            'application': forms.Select(attrs={'class': 'form-select'}),
            'domaine': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'app.exemple.com'}),
            'emetteur': forms.TextInput(attrs={'class': 'form-input', 'placeholder': "Let's Encrypt, DigiCert…"}),
            'type_certificat': forms.Select(attrs={'class': 'form-select'}),
            'algorithme': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'RSA 2048, ECDSA P-256…'}),
            'date_emission': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_expiration': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'auto_renouvellement': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Notes complémentaires…'}),
        }

    def __init__(self, *args, application=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = _applications_avec_ssl()
        if application:
            qs = qs | Application.objects.filter(pk=application.pk)
        self.fields['application'].queryset = qs.distinct().order_by('nom')

        if application and not self.instance.pk:
            self.fields['application'].initial = application.pk
            if len(qs) == 1:
                self.fields['application'].widget = forms.HiddenInput()

        for field_name in self.fields:
            if field_name not in ('auto_renouvellement', 'notes'):
                self.fields[field_name].required = True
        self.fields['notes'].required = False

    def clean_domaine(self):
        domaine = self.cleaned_data.get('domaine', '').strip().lower()
        if not domaine:
            raise ValidationError('Le domaine est obligatoire.')
        if not DOMAIN_NAME_RE.match(domaine):
            raise ValidationError('Le domaine est invalide. Ex: app.exemple.com')
        return domaine

    def clean_emetteur(self):
        emetteur = self.cleaned_data.get('emetteur', '').strip()
        if not emetteur:
            raise ValidationError('Le fournisseur SSL est obligatoire.')
        return emetteur

    def clean_algorithme(self):
        algorithme = self.cleaned_data.get('algorithme', '').strip()
        if not algorithme:
            raise ValidationError("L'algorithme est obligatoire.")
        return algorithme

    def clean(self):
        cleaned_data = super().clean()
        date_emission = cleaned_data.get('date_emission')
        date_expiration = cleaned_data.get('date_expiration')
        application = cleaned_data.get('application')

        if date_emission and date_expiration and date_expiration <= date_emission:
            raise ValidationError("La date d'expiration doit être postérieure à la date d'émission.")

        if application and not application.has_ssl:
            raise ValidationError(
                "Cette application n'est pas marquée comme nécessitant un SSL. "
                "Activez l'option dans la fiche application."
            )

        if application and not self.instance.pk:
            if CertificatSSL.objects.filter(application=application).exists():
                raise ValidationError('Un certificat SSL existe déjà pour cette application.')

        return cleaned_data
