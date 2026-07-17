from django.contrib import admin
from .models import Domaine


@admin.register(Domaine)
class DomaineAdmin(admin.ModelAdmin):
    list_display = ('nom', 'registrar', 'responsable', 'date_expiration', 'renouvellement_auto')
    search_fields = ('nom', 'registrar', 'dns', 'responsable')
    list_filter = ('renouvellement_auto',)
    ordering = ('nom',)
