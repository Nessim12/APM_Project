from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('matricule', 'username', 'email', 'nom_complet', 'role', 'departement', 'telephone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Supplémentaires', {'fields': ('role', 'departement', 'telephone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Supplémentaires', {'fields': ('role', 'departement', 'telephone')}),
    )

    def nom_complet(self, obj):
        return f"{obj.last_name} {obj.first_name}"
    nom_complet.short_description = 'Nom Complet'

admin.site.register(User, CustomUserAdmin)
