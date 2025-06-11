# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('join/<uuid:session_id>/', views.join, name='join'),
    
    path('lobby/<uuid:session_id>/', views.lobby, name='lobby'),
    path('players/<uuid:session_id>/', views.get_state, name='get_state'),
    path('kick/<uuid:session_id>/', views.kick_player, name='kick_player'),
    
    path('start_game/<uuid:session_id>/', views.start_game, name='start_game'),
    path('role/<uuid:session_id>/', views.role, name='role'),
    
    path('end_game/<uuid:session_id>/', views.end_game, name='end_game'),
    path('ended/<uuid:session_id>/', views.ended, name='ended'),
]