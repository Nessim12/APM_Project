from django.urls import path

from . import views

app_name = 'contrats'

urlpatterns = [
    path('', views.contract_dashboard, name='contrat_dashboard'),
    path('fournisseurs/', views.fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/add/', views.fournisseur_create, name='fournisseur_create'),
    path('fournisseurs/<int:pk>/edit/', views.fournisseur_update, name='fournisseur_update'),
    path('fournisseurs/<int:pk>/delete/', views.fournisseur_delete, name='fournisseur_delete'),
    path('types/<str:contract_type>/', views.contract_type_list, name='contrat_type_list'),
    path('add/', views.contract_create, name='contract_create'),
    path('<uuid:pk>/', views.contract_detail, name='contract_detail'),
    path('<uuid:pk>/edit/', views.contract_update, name='contract_update'),
    path('<uuid:pk>/delete/', views.contract_delete, name='contract_delete'),
]
