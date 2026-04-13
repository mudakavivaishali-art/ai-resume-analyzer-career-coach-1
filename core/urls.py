from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Modules (IMPORTANT FIX HERE 👇)
    path('builder/', views.resume_builder_view, name='resume_builder'),
    path('analyzer/', views.resume_analyzer_view, name='resume_analyzer'),
    path('interview/', views.interview_practice_view, name='interview_practice'),
    path('settings/', views.settings_view, name='user_settings'),
    path('settings/edit/', views.edit_profile, name='edit_profile'),
    # Password change
    path('password_change/', views.change_password, name='password_change'),

    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
]
