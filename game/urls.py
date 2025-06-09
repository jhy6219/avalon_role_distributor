# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('join/<uuid:session_id>/', views.join, name='join'),
    path('lobby/<uuid:session_id>/', views.lobby, name='lobby'),
]