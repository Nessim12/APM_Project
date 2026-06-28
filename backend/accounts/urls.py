from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/users/add/', views.user_create, name='user_create'),
    path('dashboard/users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('dashboard/users/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('dashboard/users/import/', views.user_import_excel, name='user_import_excel'),
]
