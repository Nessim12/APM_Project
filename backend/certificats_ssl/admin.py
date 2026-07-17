from django.contrib import admin

from .models import AlerteSSLEnvoyee, CertificatSSL, NotificationAdmin


@admin.register(CertificatSSL)
class CertificatSSLAdmin(admin.ModelAdmin):
    list_display = ('domaine', 'application', 'emetteur', 'type_certificat', 'statut', 'date_expiration', 'auto_renouvellement')
    list_filter = ('statut', 'type_certificat', 'auto_renouvellement')
    search_fields = ('domaine', 'emetteur', 'application__nom')


@admin.register(AlerteSSLEnvoyee)
class AlerteSSLEnvoyeeAdmin(admin.ModelAdmin):
    list_display = ('certificat', 'niveau', 'canal', 'envoyee_le')
    list_filter = ('niveau', 'canal')
    search_fields = ('certificat__domaine', 'certificat__application__nom')


@admin.register(NotificationAdmin)
class NotificationAdminAdmin(admin.ModelAdmin):
    list_display = ('titre', 'destinataire', 'niveau', 'lue', 'created_at')
    list_filter = ('niveau', 'lue')
    search_fields = ('titre', 'destinataire__email', 'certificat__domaine')
