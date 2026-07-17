from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import UserActivityLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    UserActivityLog.objects.create(
        user=user,
        action=UserActivityLog.ActionChoices.LOGIN,
        path=request.path_info,
        description=f"Connexion de l'utilisateur : {user.get_full_name()} ({user.get_role_display()})",
        ip_address=ip
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        UserActivityLog.objects.create(
            user=user,
            action=UserActivityLog.ActionChoices.LOGOUT,
            path=request.path_info,
            description=f"Déconnexion de l'utilisateur : {user.get_full_name()} ({user.get_role_display()})",
            ip_address=ip
        )
