from django.apps import AppConfig


class CertificatsSslConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certificats_ssl'
    label = 'ssl'
    verbose_name = 'Gestion SSL'
