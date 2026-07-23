from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from .models import Application


def _user_queryset():
    """Utilisateurs éligibles comme responsables."""
    return User.objects.filter(is_active=True).exclude(is_superuser=True).order_by('last_name', 'first_name')


class ApplicationForm(forms.ModelForm):
    """Formulaire de création et de modification d'une application."""

    environnements = forms.MultipleChoiceField(
        choices=[
            ('DEV', 'DEV'),
            ('RECETTE', 'RECETTE'),
            ('PREPROD', 'PREPROD'),
            ('PROD', 'PROD'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox-list'}),
        required=False,
        label="Environnements associés"
    )

    class Meta:
        model = Application
        fields = [
            'nom',
            'description',
            'criticite',
            'statut',
            'date_mise_en_production',
            'date_fin_vie',
            'direction_metier',
            'nombre_utilisateurs',
            'has_ssl',
            'responsable_metier',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-input', 'placeholder': "Nom de l'application"}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Description détaillée'}),
            'criticite': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'date_mise_en_production': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'date_fin_vie': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'direction_metier': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Direction métier'}),
            'nombre_utilisateurs': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'has_ssl': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'responsable_metier': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = _user_queryset()
        for field_name in (
            'responsable_metier',
        ):
            self.fields[field_name].queryset = users
            self.fields[field_name].required = True

        # Initialiser les environnements
        if self.instance.pk:
            self.fields['environnements'].initial = list(
                self.instance.environnements.filter(nom__in=['DEV', 'RECETTE', 'PREPROD', 'PROD']).values_list('nom', flat=True)
            )

        # Le statut « Archivé » n'est pas sélectionnable manuellement via le formulaire
        statut_choices = [
            (value, label)
            for value, label in Application.StatutChoices.choices
            if value != Application.StatutChoices.ARCHIVE
        ]
        self.fields['statut'].choices = statut_choices

        for field_name in self.fields:
            if field_name not in ('date_fin_vie', 'has_ssl', 'date_mise_en_production', 'environnements'):
                self.fields[field_name].required = True
        self.fields['date_fin_vie'].required = False
        self.fields['has_ssl'].required = False
        self.fields['date_mise_en_production'].required = False

    def save(self, commit=True):
        application = super().save(commit=commit)
        if commit:
            self.save_environnements(application)
        else:
            original_save_m2m = self.save_m2m
            def save_m2m_with_envs():
                original_save_m2m()
                self.save_environnements(application)
            self.save_m2m = save_m2m_with_envs
        return application

    def save_environnements(self, application):
        selected_envs = self.cleaned_data.get('environnements', [])
        existing_envs = {env.nom: env for env in application.environnements.all()}
        
        from environments.models import Environnement
        for env_name in selected_envs:
            if env_name not in existing_envs:
                Environnement.objects.create(
                    nom=env_name,
                    application=application,
                    url=f'http://localhost/{application.nom.lower().replace(" ", "-")}-{env_name.lower()}',
                    adresse_ip='127.0.0.1',
                    os='Linux',
                    cpu='2 vCPU',
                    ram='4 Go',
                    hebergeur='Interne',
                    type_hebergement='ON_PREMISE'
                )
        
        for env_name, env in existing_envs.items():
            if env_name in ['DEV', 'RECETTE', 'PREPROD', 'PROD'] and env_name not in selected_envs:
                env.delete()

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if not nom:
            raise ValidationError('Le nom est obligatoire.')
        return nom

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise ValidationError('La description est obligatoire.')
        return description

    def clean_direction_metier(self):
        direction = self.cleaned_data.get('direction_metier', '').strip()
        if not direction:
            raise ValidationError('La direction métier est obligatoire.')
        return direction

    def clean(self):
        cleaned_data = super().clean()
        date_prod = cleaned_data.get('date_mise_en_production')
        date_fin = cleaned_data.get('date_fin_vie')

        if date_prod and date_fin and date_fin <= date_prod:
            raise ValidationError(
                'La date de fin de vie doit être postérieure à la date de mise en production.'
            )
        return cleaned_data


class ApplicationFilterForm(forms.Form):
    """Formulaire de filtrage multicritères pour la liste des applications."""

    nom = forms.CharField(
        required=False,
        label='Nom',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Rechercher par nom…'}),
    )
    criticite = forms.ChoiceField(
        required=False,
        label='Criticité',
        choices=[('', '— Toutes —')] + list(Application.CriticiteChoices.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    statut = forms.ChoiceField(
        required=False,
        label='Statut',
        choices=[('', '— Tous —')] + list(Application.StatutChoices.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    direction_metier = forms.CharField(
        required=False,
        label='Direction métier',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Direction métier…'}),
    )
    responsable = forms.ModelChoiceField(
        required=False,
        label='Responsable assigné',
        queryset=_user_queryset(),
        empty_label='— Tous —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
