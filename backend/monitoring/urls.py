from django.urls import path
from . import views

urlpatterns = [
    path('vm/register/', views.register_vm, name='vm_register'),
    path('vm/heartbeat/', views.heartbeat, name='vm_heartbeat'),
    path('vm/metrics/', views.receive_metrics, name='vm_metrics'),
    path('vm/metrics/summary/', views.metrics_summary, name='vm_metrics_summary'),
    path('vm/', views.vm_list, name='vm_list'),
    path('vm/<int:pk>/metrics/summary/', views.vm_metrics_summary, name='vm_metrics_vm_summary'),
    path('vm/<int:pk>/metrics/', views.vm_metrics_history, name='vm_metrics_history'),
]
