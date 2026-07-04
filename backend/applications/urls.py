from django.urls import path

from . import views

urlpatterns = [
    path('', views.application_list, name='application_list'),
    path('add/', views.application_create, name='application_create'),
    path('<uuid:pk>/', views.application_detail, name='application_detail'),
    path('<uuid:pk>/edit/', views.application_update, name='application_update'),
    path('<uuid:pk>/archive/', views.application_archive, name='application_archive'),
]
