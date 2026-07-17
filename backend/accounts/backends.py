from django.contrib.auth.backends import ModelBackend
from .models import User


class MatriculeOrEmailBackend(ModelBackend):
    """
    Allow login with either:
      - matricule  (ex: TOPNET_1)
      - email      (ex: admin@example.com)
    + password
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # Try to find user by matricule first, then by email
        user = (
            User.objects.filter(matricule__iexact=username).first()
            or User.objects.filter(email__iexact=username).first()
        )

        if user and user.check_password(password):
            if not self.user_can_authenticate(user):
                if request is not None:
                    request.auth_failure_reason = 'inactive'
                return None
            if request is not None:
                request.auth_failure_reason = 'invalid'
            return user

        return None
