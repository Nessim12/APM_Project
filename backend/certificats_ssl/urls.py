from django.urls import path

from . import views

urlpatterns = [
    path('', views.ssl_list, name='ssl_list'),
    path('notifications/', views.ssl_notifications, name='ssl_notifications'),
    path('notifications/<int:pk>/read/', views.ssl_notification_mark_read, name='ssl_notification_mark_read'),
    path('notifications/read-all/', views.ssl_notifications_mark_all_read, name='ssl_notifications_mark_all_read'),
    path('add/', views.ssl_create, name='ssl_create'),
    path('<uuid:pk>/', views.ssl_detail, name='ssl_detail'),
    path('<uuid:pk>/edit/', views.ssl_update, name='ssl_update'),
]
