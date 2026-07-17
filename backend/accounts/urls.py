from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/users/add/', views.user_create, name='user_create'),
    path('dashboard/users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('dashboard/users/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('dashboard/users/import/', views.user_import_excel, name='user_import_excel'),
    path('support/messages/', views.support_message_list, name='support_message_list'),
    path('support/messages/new/', views.support_message_create, name='support_message_create'),
    path('support/messages/<int:pk>/read/', views.support_message_mark_read, name='support_message_mark_read'),
]
