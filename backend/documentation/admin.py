from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_fichier', 'categorie', 'type_gestion', 'date_upload', 'uploaded_by')
    list_filter = ('categorie', 'type_gestion', 'type_fichier')
    search_fields = ('nom', 'description')
    readonly_fields = ('date_upload', 'type_fichier', 'taille_octets')
