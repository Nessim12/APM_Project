from django.urls import path

from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('nouveau/', views.document_create, name='document_create'),
    path('<uuid:pk>/', views.document_detail, name='document_detail'),
    path('<uuid:pk>/modifier/', views.document_update, name='document_update'),
    path('<uuid:pk>/supprimer/', views.document_delete, name='document_delete'),
    path('<uuid:pk>/voir/', views.document_preview, name='document_preview'),
    path('<uuid:pk>/telecharger/', views.document_download, name='document_download'),
]
