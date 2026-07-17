from accounts.models import SupportMessage, User
from .alerts import ensure_in_app_notifications
from .models import NotificationAdmin


def ssl_notifications(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.role not in {User.RoleChoices.ADMIN, User.RoleChoices.ADMIN_SYS}:
        return {}

    ensure_in_app_notifications()

    unread = NotificationAdmin.objects.filter(
        destinataire=request.user,
        lue=False,
    ).count()
    support_unread_messages = 0
    if request.user.role in {User.RoleChoices.ADMIN, User.RoleChoices.ADMIN_SYS}:
        support_unread_messages = SupportMessage.objects.filter(lue=False).count()

    return {
        'ssl_unread_notifications': unread,
        'support_unread_messages': support_unread_messages,
    }
