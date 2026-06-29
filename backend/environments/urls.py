from django.urls import path

from . import views

urlpatterns = [
    path('', views.environment_list, name='environment_list'),
    path('add/', views.environment_create, name='environment_create'),
    path('<uuid:pk>/', views.environment_detail, name='environment_detail'),
    path('<uuid:pk>/edit/', views.environment_update, name='environment_update'),
    path('<uuid:pk>/delete/', views.environment_delete, name='environment_delete'),

    path('serveurs/', views.server_list, name='server_list'),
    path('serveurs/add/', views.server_create, name='server_create'),
    path('serveurs/<int:pk>/edit/', views.server_update, name='server_update'),
    path('serveurs/<int:pk>/delete/', views.server_delete, name='server_delete'),
]