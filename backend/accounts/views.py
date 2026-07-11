import secrets
import string
import random
import openpyxl
import threading

from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import SupportMessage, User
from .forms import UserForm, ProfileForm, ExcelImportForm, UserFilterForm


# ─── Helpers ───────────────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and user.role != User.RoleChoices.TECH


def can_manage_users(user):
    return user.is_authenticated and user.role == User.RoleChoices.ADMIN


def can_send_support_message(user):
    return user.is_authenticated and user.role == User.RoleChoices.TECH


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
    def _send():
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception as e:
            print(f"[EMAIL ERROR] Could not send email to {user.email}: {e}")
            
    threading.Thread(target=_send).start()


import urllib.request
import urllib.parse
import json

# ─── CAPTCHA helper ────────────────────────────────────────────────────────────────

def verify_recaptcha(response_token):
    # Remplacement par la clé secrète de test globale
    secret = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
    url = 'https://www.google.com/recaptcha/api/siteverify'
    data = urllib.parse.urlencode({
        'secret': secret,
        'response': response_token
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get('success', False)
    except Exception:
        return False

# ─── Login (redirect by role) ──────────────────────────────────────────────────────

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Validate Google reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response or not verify_recaptcha(recaptcha_response):
            context = self.get_context_data()
            context['auth_error_message'] = "Veuillez valider le CAPTCHA pour continuer."
            return self.render_to_response(context)

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reason = getattr(self.request, 'auth_failure_reason', None)
        if reason == 'inactive':
            context['auth_error_message'] = "Votre compte n'est pas activé. Veuillez contacter l'administrateur."
        elif self.request.method == 'POST' and self.request.user.is_anonymous:
            if 'auth_error_message' not in context:
                context['auth_error_message'] = "Identifiant ou mot de passe incorrect."
        return context

    def get_success_url(self):
        return '/dashboard/'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


# ─── User Management Dashboard ────────────────────────────────────────────────

@login_required
def dashboard(request):
    users_list = User.objects.exclude(is_superuser=True)
    
    filter_form = UserFilterForm(request.GET)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data.get('q'):
            q = data['q']
            users_list = users_list.filter(
                Q(matricule__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(departement__icontains=q)
            )
            
        if data.get('role'):
            users_list = users_list.filter(role=data['role'])
            
        if data.get('statut'):
            # statut: '1' -> Actif, '0' -> Inactif
            is_active = True if data['statut'] == '1' else False
            users_list = users_list.filter(is_active=is_active)
    
    # Sort
    sort_by = request.GET.get('sort', '-date_joined')
    valid_sorts = ['matricule', '-matricule', 'first_name', '-first_name', 'email', '-email', 'departement', '-departement', 'role', '-role', 'is_active', '-is_active', 'date_joined', '-date_joined']
    if sort_by in valid_sorts:
        users_list = users_list.order_by(sort_by)
    else:
        users_list = users_list.order_by('-date_joined')

    def get_sort_url(field):
        p = request.GET.copy()
        if 'page' in p:
            del p['page']
        if p.get('sort') == field:
            p['sort'] = f"-{field}"
        else:
            p['sort'] = field
        return f"?{p.urlencode()}"

    sort_urls = {
        'matricule': get_sort_url('matricule'),
        'first_name': get_sort_url('first_name'),
        'email': get_sort_url('email'),
        'departement': get_sort_url('departement'),
        'role': get_sort_url('role'),
        'is_active': get_sort_url('is_active'),
    }

    paginator = Paginator(users_list, 5)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    url_params = params.urlencode()
    url_params_str = f"&{url_params}" if url_params else ""

    return render(request, 'accounts/dashboard.html', {
        'users': users, 
        'page_obj': users, 
        'url_params': url_params_str,
        'filter_form': filter_form,
        'sort_by': sort_by,
        'sort_urls': sort_urls,
        'can_manage_users': can_manage_users(request.user),
        'current_role': request.user.role,
    })


@login_required
@user_passes_test(can_manage_users, login_url='dashboard')
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
@user_passes_test(can_manage_users, login_url='dashboard')
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
@user_passes_test(can_manage_users, login_url='dashboard')
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activé' if user.is_active else 'désactivé'
        messages.success(request, f'Utilisateur {status} avec succès.')
    return redirect('dashboard')


@login_required
@user_passes_test(can_manage_users, login_url='dashboard')
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
                if count > 0:
                    messages.success(request, f'{count} utilisateur(s) importé(s) avec succès ! Emails envoyés.')

                if errors:
                    if count == 0:
                        error_msg = "Import annulé — tous les utilisateurs existent déjà :\n" + "\n".join(errors)
                    else:
                        error_msg = "Certains utilisateurs n'ont pas été importés (doublons) :\n" + "\n".join(errors)
                    messages.warning(request, error_msg)
                elif count == 0:
                    messages.info(request, 'Aucun utilisateur à importer dans le fichier.')

                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation: {e}")
    else:
        form = ExcelImportForm()
    return render(request, 'accounts/import_excel.html', {'form': form})


# ─── User: Own Profile ────────────────────────────────────────────────────────

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.role in {User.RoleChoices.ADMIN, User.RoleChoices.ADMIN_SYS}, login_url='dashboard')
def support_message_list(request):
    messages_qs = SupportMessage.objects.select_related('sender').all()
    unread_count = messages_qs.filter(lue=False).count()
    return render(request, 'accounts/support_message_list.html', {
        'support_messages': messages_qs,
        'unread_count': unread_count,
    })


@login_required
@user_passes_test(can_send_support_message, login_url='dashboard')
def support_message_create(request):
    if request.method == 'POST':
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()
        if subject and message:
            SupportMessage.objects.create(
                sender=request.user,
                subject=subject,
                message=message,
            )
            messages.success(request, 'Votre message a été envoyé à l’administrateur.')
            return redirect('support_message_create')
        messages.error(request, 'Veuillez renseigner le sujet et le message.')

    return render(request, 'accounts/support_message_form.html')


@login_required
@user_passes_test(lambda user: user.role in {User.RoleChoices.ADMIN, User.RoleChoices.ADMIN_SYS}, login_url='dashboard')
def support_message_mark_read(request, pk):
    support_message = get_object_or_404(SupportMessage, pk=pk)
    support_message.lue = True
    support_message.read_at = timezone.now()
    support_message.save(update_fields=['lue', 'read_at'])
    messages.success(request, 'Message marqué comme lu.')
    return redirect('support_message_list')
