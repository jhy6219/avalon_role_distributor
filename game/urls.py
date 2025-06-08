# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create_session/', views.create_session, name='create_session'),
    path('join_session/<uuid:session_id>/', views.join_session, name='join_session'),
    path('game_lobby/<uuid:session_id>/', views.game_lobby, name='game_lobby'),
]