from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.api_home, name='api_home'),
    path('analyze/', api_views.analyze_resume, name='analyze_resume'),
]