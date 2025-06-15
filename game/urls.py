from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_room, name='create_room'),
    path('join/', views.join_room, name='join_room'),
    path('room/<str:room_code>/', views.game_room, name='game_room'),
    path('api/room/<str:room_code>/start/', views.start_game, name='start_game'),
    path('api/room/<str:room_code>/vote/', views.vote, name='vote'),
    path('api/room/<str:room_code>/mission/', views.mission_action, name='mission_action'),
    path('api/room/<str:room_code>/restart/', views.restart_game, name='restart_game'),
]