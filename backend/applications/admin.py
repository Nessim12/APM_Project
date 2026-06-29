from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'criticite', 'statut', 'direction_metier', 'date_mise_en_production')
    list_filter = ('criticite', 'statut', 'direction_metier')
    search_fields = ('nom', 'description', 'direction_metier')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def get_queryset(self, request):
        return Application.all_objects.get_queryset()
