# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('join/<uuid:session_id>/', views.join, name='join'),
    path('lobby/<uuid:session_id>/', views.lobby, name='lobby'),
    path('players/<uuid:session_id>/', views.get_players, name='get_players'),
    path('kick/<uuid:session_id>/', views.kick_player, name='kick_player'),
]