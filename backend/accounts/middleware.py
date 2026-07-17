from django.shortcuts import redirect


class AdminRoleAccessMiddleware:
    """Restrict the ADMIN role to user management pages only."""

    allowed_prefixes = (
        '/dashboard/',
        '/profile/',
        '/login/',
        '/logout/',
        '/password-reset/',
        '/reset/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user.role == 'ADMIN':
            path = request.path_info
            if not path.startswith(self.allowed_prefixes):
                return redirect('dashboard')

        return self.get_response(request)


class UserActivityLoggingMiddleware:
    """Log page accesses and actions for authenticated users, ignoring high-frequency API or static requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            path = request.path_info
            
            ignored_prefixes = (
                '/static/',
                '/media/',
                '/api/',
                '/__debug__/',
                '/favicon.ico',
            )
            
            if not path.startswith(ignored_prefixes):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                else:
                    ip = request.META.get('REMOTE_ADDR')

                from .models import UserActivityLog

                # Determine action type (POST requests usually represent database modifying actions)
                if request.method == 'POST':
                    action = UserActivityLog.ActionChoices.ACTION
                    description = f"Action POST sur la route : {path}"
                else:
                    action = UserActivityLog.ActionChoices.ACCESS
                    description = f"Page consultée : {path}"

                # Avoid logging logouts via ACCESS as they are already logged via signal
                if not (path == '/logout/' and request.method == 'POST'):
                    UserActivityLog.objects.create(
                        user=user,
                        action=action,
                        path=path,
                        description=description,
                        ip_address=ip
                    )

        return response