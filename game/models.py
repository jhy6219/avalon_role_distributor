# game/models.py
from django.db import models
import uuid

class GameSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 다른 게임 관련 필드를 여기에 추가할 수 있습니다 (예: created_at, is_active 등)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Game Session: {self.session_id}"

class Player(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=50, unique=False) # 세션 내에서만 유니크
    password = models.CharField(max_length=128) # 비밀번호는 해싱해서 저장하는 것이 좋습니다.
    # 나중에 Player의 Session Key를 저장하여 재접속 시 활용할 수 있습니다.
    session_key = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        unique_together = ('game_session', 'nickname') # 한 세션 내에서 닉네임 중복 방지

    def __str__(self):
        return f"{self.nickname} in {self.game_session.session_id}"