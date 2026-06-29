from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        ADMIN  = 'ADMIN',  _('Admin')
        TECH   = 'TECH',   _('Tech')
        MEMBRE = 'MEMBRE', _('Membre')

    role        = models.CharField(max_length=10, choices=RoleChoices.choices, default=RoleChoices.MEMBRE)
    telephone   = models.CharField(max_length=20, blank=True, null=True)
    departement = models.CharField(max_length=100, blank=True, null=True)
    matricule   = models.CharField(max_length=30, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Save first so that self.pk is assigned
        super().save(*args, **kwargs)
        # Generate matricule automatically after first save
        if not self.matricule:
            self.matricule = f"TOPNET_{self.pk}"
            # Update only the matricule field to avoid recursion
            User.objects.filter(pk=self.pk).update(matricule=self.matricule)

    def __str__(self):
        return f"{self.matricule} — {self.get_full_name()} ({self.get_role_display()})"
