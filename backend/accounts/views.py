import secrets
import string
import openpyxl

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.conf import settings

from .models import User
from .forms import UserForm, ProfileForm, ExcelImportForm


# ─── Helpers ───────────────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and user.role == User.RoleChoices.ADMIN


def generate_password(length=10):
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_welcome_email(user, password):
    subject = "Bienvenue sur APM Project — Vos accès"
    message = f"""Bonjour {user.first_name} {user.last_name},

Votre compte sur la plateforme APM Project a été créé avec succès.

Voici vos informations de connexion :

  Matricule   : {user.matricule}
  Email       : {user.email}
  Mot de passe: {password}

Connectez-vous sur : http://localhost:8000/login/

Nous vous recommandons de changer votre mot de passe dès votre première connexion.

Cordialement,
L'équipe APM Project
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    except Exception as e:
        print(f"[EMAIL ERROR] Could not send email to {user.email}: {e}")


# ─── Login (redirect by role) ──────────────────────────────────────────────────

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == User.RoleChoices.ADMIN:
            return '/dashboard/'
        return '/profile/'


# ─── Admin: User Management Dashboard ─────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    users = User.objects.exclude(is_superuser=True).order_by('-date_joined')
    return render(request, 'accounts/dashboard.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            base_username = user.email.split('@')[0] if user.email else f"{user.first_name}.{user.last_name}".lower()
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
            password = generate_password()
            user.set_password(password)
            user.save()
            send_welcome_email(user, password)
            messages.success(request, f'Utilisateur créé ! Email envoyé à {user.email}.')
            return redirect('dashboard')
    else:
        form = UserForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(is_admin)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Utilisateur mis à jour !')
            return redirect('dashboard')
    else:
        form = UserForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Modifier', 'edit_user': user})


@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activé' if user.is_active else 'désactivé'
        messages.success(request, f'Utilisateur {status} avec succès.')
    return redirect('dashboard')


@login_required
@user_passes_test(is_admin)
def user_import_excel(request):
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                wb = openpyxl.load_workbook(excel_file)
                sheet = wb.active
                count = 0
                errors = []
                for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    first_name, last_name, email, telephone, departement, role = (list(row) + [None]*6)[:6]
                    if not email:
                        continue
                    email = str(email).strip()
                    if User.objects.filter(email=email).exists():
                        errors.append(f"Ligne {i}: {email} existe déjà.")
                        continue
                    role_value = str(role).strip().upper() if role else User.RoleChoices.MEMBRE
                    valid_roles = [r.value for r in User.RoleChoices]
                    if role_value not in valid_roles:
                        role_value = User.RoleChoices.MEMBRE
                    password = generate_password()
                    base_username = email.split('@')[0]
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    user = User(
                        first_name=str(first_name or '').strip(),
                        last_name=str(last_name or '').strip(),
                        email=email,
                        username=username,
                        telephone=str(telephone or '').strip(),
                        departement=str(departement or '').strip(),
                        role=role_value,
                    )
                    user.set_password(password)
                    user.save()
                    send_welcome_email(user, password)
                    count += 1
                for err in errors:
                    messages.warning(request, err)
                messages.success(request, f'{count} utilisateur(s) importé(s) ! Emails envoyés.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation: {e}")
    else:
        form = ExcelImportForm()
    return render(request, 'accounts/import_excel.html', {'form': form})


# ─── User: Own Profile (MEMBRE / TECH) ────────────────────────────────────────

@login_required
def profile(request):
    if request.user.role == User.RoleChoices.ADMIN:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
