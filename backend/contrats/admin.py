from django.contrib import admin

from .models import Contract, Fournisseur


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'responsable')
    search_fields = ('nom', 'email', 'telephone', 'responsable')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('numero_contrat', 'contract_type', 'application', 'fournisseur', 'date_debut', 'date_fin', 'statut')
    list_filter = ('contract_type', 'statut', 'application')
    search_fields = ('numero_contrat', 'application__nom', 'fournisseur__nom', 'sla')
    ordering = ('-date_debut',)
