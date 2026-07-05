import re
from django import forms
from django.core.exceptions import ValidationError
from .models import User


# ─── Validators ────────────────────────────────────────────────────────────────

def validate_telephone(value):
    """Accepts digits, spaces, +, -, () only."""
    if value and not re.fullmatch(r'[\d\s\+\-\(\)]{6,20}', value):
        raise ValidationError(
            "Le numéro de téléphone est invalide. Ex: +216 22 333 444"
        )


# ─── Admin: Create / Update user ───────────────────────────────────────────────

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'departement', 'role']
        widgets = {
            'first_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'}),
            'email':       forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'exemple@email.com'}),
            'telephone':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+216 XX XXX XXX'}),
            'departement': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Département'}),
            'role':        forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields required except telephone and departement
        self.fields['first_name'].required  = True
        self.fields['last_name'].required   = True
        self.fields['email'].required       = True
        self.fields['role'].required        = True
        self.fields['telephone'].required   = False
        self.fields['departement'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cet email est déjà utilisé par un autre utilisateur.")
        return email

    def clean_telephone(self):
        tel = self.cleaned_data.get('telephone', '').strip()
        if tel:
            validate_telephone(tel)
            qs = User.objects.filter(telephone=tel)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return tel

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '').strip()
        if not value:
            raise ValidationError("Le prénom est obligatoire.")
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '').strip()
        if not value:
            raise ValidationError("Le nom est obligatoire.")
        return value


# ─── User: Edit own profile ────────────────────────────────────────────────────

class ProfileForm(forms.ModelForm):
    """Form used by MEMBRE / TECH to edit their own profile."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'departement']
        widgets = {
            'first_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'}),
            'email':       forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'exemple@email.com'}),
            'telephone':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+216 XX XXX XXX'}),
            'departement': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Département'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_telephone(self):
        tel = self.cleaned_data.get('telephone', '').strip()
        if tel:
            validate_telephone(tel)
            qs = User.objects.filter(telephone=tel).exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return tel


# ─── Excel Import ──────────────────────────────────────────────────────────────

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Fichier Excel',
        widget=forms.FileInput(attrs={'class': 'file-input', 'accept': '.xlsx, .xls'})
    )


# ─── Filter Form ───────────────────────────────────────────────────────────────

class UserFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Recherche',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Matricule, nom, email…'}),
    )
    role = forms.ChoiceField(
        required=False,
        label='Rôle',
        choices=[('', '— Tous —')] + list(User.RoleChoices.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    statut = forms.ChoiceField(
        required=False,
        label='Statut',
        choices=[('', '— Tous —'), ('1', 'Actif'), ('0', 'Inactif')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
