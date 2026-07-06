from accounts.models import User
from .alerts import ensure_in_app_notifications
from .models import NotificationAdmin


def ssl_notifications(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.role != User.RoleChoices.ADMIN:
        return {}

    ensure_in_app_notifications()

    unread = NotificationAdmin.objects.filter(
        destinataire=request.user,
        lue=False,
    ).count()

    return {'ssl_unread_notifications': unread}
