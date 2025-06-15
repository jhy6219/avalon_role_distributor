from django.db import models
import json
import random

class GameRoom(models.Model):
    room_code = models.CharField(max_length=6, unique=True)
    host_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    game_state = models.TextField(default='{}')  # JSON field
    include_oberon = models.BooleanField(default=False)
    include_mordred = models.BooleanField(default=False)
    
    def get_game_state(self):
        return json.loads(self.game_state) if self.game_state else {}
    
    def set_game_state(self, state):
        self.game_state = json.dumps(state)
        self.save()

class Player(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50)
    is_host = models.BooleanField(default=False)
    role = models.CharField(max_length=20, blank=True)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'name']