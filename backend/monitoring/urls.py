from django.urls import path
from . import views

urlpatterns = [
    path('vm/register/', views.register_vm, name='vm_register'),
    path('vm/heartbeat/', views.heartbeat, name='vm_heartbeat'),
    path('vm/metrics/', views.receive_metrics, name='vm_metrics'),
    path('vm/', views.vm_list, name='vm_list'),
    path('vm/<int:pk>/metrics/', views.vm_metrics_history, name='vm_metrics_history'),
]
