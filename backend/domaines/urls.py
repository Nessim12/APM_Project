from django.urls import path

from . import views

urlpatterns = [
    path('', views.domaine_list, name='domaine_list'),
    path('add/', views.domaine_create, name='domaine_create'),
    path('<int:pk>/', views.domaine_detail, name='domaine_detail'),
    path('<int:pk>/edit/', views.domaine_update, name='domaine_update'),
    path('<int:pk>/delete/', views.domaine_delete, name='domaine_delete'),
]
