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