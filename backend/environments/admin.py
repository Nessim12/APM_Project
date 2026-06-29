from django.contrib import admin

from .models import Environnement, Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'adresse_ip', 'systeme_exploitation')
    search_fields = ('hostname', 'adresse_ip')


@admin.register(Environnement)
class EnvironnementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'application', 'serveur', 'type_hebergement', 'docker', 'kubernetes')
    list_filter = ('type_hebergement', 'docker', 'kubernetes')
    search_fields = ('nom', 'application__nom', 'serveur__hostname', 'hebergeur')
    raw_id_fields = ('application', 'serveur')
