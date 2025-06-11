# game/models.py
from django.db import models
import uuid

class GameSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    host_nickname = models.CharField(max_length=50, null=True, blank=True)

    option1 = models.BooleanField(default=False)
    option2 = models.BooleanField(default=False)
    option3 = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_started = models.BooleanField(default=False)

    def __str__(self):
        return f"Game Session: {self.session_id}"


class Player(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=50, unique=False)
    pin = models.CharField(max_length=128)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    role = models.CharField(max_length=128, blank=True)
    role_intro  = models.CharField(max_length=1024, blank=True)
    role_detail = models.CharField(max_length=1024, blank=True)
    role_image  = models.CharField(max_length=1024, blank=True)

    class Meta:
        unique_together = ('game_session', 'nickname') # 한 세션 내에서 닉네임 중복 방지

    def __str__(self):
        return f"{self.nickname} in {self.game_session.session_id}"