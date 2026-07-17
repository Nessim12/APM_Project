from django import forms
from django.db.models import Q

from applications.models import Application
from .models import Contract, Fournisseur


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'email', 'telephone', 'adresse', 'site_web', 'responsable']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom du fournisseur'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Téléphone'}),
            'adresse': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Adresse'}),
            'site_web': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Site web'}),
            'responsable': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Responsable'}),
        }


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'numero_contrat',
            'contract_type',
            'date_debut',
            'date_fin',
            'cout_annuel',
            'sla',
            'statut',
            'application',
            'fournisseur',
        ]
        widgets = {
            'numero_contrat': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Numéro de contrat'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'cout_annuel': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'sla': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SLA'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'application': forms.Select(attrs={'class': 'form-select'}),
            'fournisseur': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_fin <= date_debut:
            raise forms.ValidationError('La date de fin doit être postérieure à la date de début.')
        return cleaned_data


class ContractFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Recherche',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Numéro, application, fournisseur…'}),
    )
    statut = forms.ChoiceField(
        required=False,
        label='Statut',
        choices=[('', '— Tous —')] + list(Contract.StatutChoices.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    application = forms.ModelChoiceField(
        required=False,
        label='Application',
        queryset=Application.objects.all().order_by('nom'),
        empty_label='— Tous —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fournisseur = forms.ModelChoiceField(
        required=False,
        label='Fournisseur',
        queryset=Fournisseur.objects.all().order_by('nom'),
        empty_label='— Tous —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    order_by = forms.ChoiceField(
        required=False,
        label='Trier par',
        choices=[
            ('', '— Défaut —'),
            ('date_debut', 'Date de début ↑'),
            ('-date_debut', 'Date de début ↓'),
            ('date_fin', 'Date de fin ↑'),
            ('-date_fin', 'Date de fin ↓'),
            ('cout_annuel', 'Coût annuel ↑'),
            ('-cout_annuel', 'Coût annuel ↓'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def filter_queryset(self, queryset):
        if not self.is_valid():
            return queryset

        data = self.cleaned_data
        q = data.get('q')
        if q:
            queryset = queryset.filter(
                Q(numero_contrat__icontains=q)
                | Q(application__nom__icontains=q)
                | Q(fournisseur__nom__icontains=q)
                | Q(sla__icontains=q)
            )

        if data.get('statut'):
            queryset = queryset.filter(statut=data['statut'])

        if data.get('application'):
            queryset = queryset.filter(application=data['application'])

        if data.get('fournisseur'):
            queryset = queryset.filter(fournisseur=data['fournisseur'])

        order_by = data.get('order_by')
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset
