from django.urls import path
from . import page_views

urlpatterns = [
    path('', page_views.monitoring_dashboard, name='monitoring_dashboard'),
]
