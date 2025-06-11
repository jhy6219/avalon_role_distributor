# game/models.py
from django.db import models
from django.utils.safestring import mark_safe
import uuid

import ftn.generate_msg as avalon_role


class GameSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    host_nickname = models.CharField(max_length=50, null=True, blank=True)

    option1 = models.BooleanField(default=False)
    option2 = models.BooleanField(default=False)
    option3 = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_started = models.BooleanField(default=False)


    def distribute_roles(self):
        players = [player.nickname for player in list(self.players.all())]
        enable_persival = self.option1 == True
        enable_morgana  = self.option2 == True
        
        if len(players) < 5:
            players += [f'dummy_{i}' for i in range(9-len(players))]

        distrb_raw = avalon_role.distributor(players, enable_persival, enable_morgana)
        distrb = avalon_role.distribution_post_process(distrb_raw)
        for assignee, description in distrb.items():
            try:
                player = Player.objects.get(game_session=self, nickname=assignee)
                player.role = description['role']
                player.role_intro = description['intro']
                player.role_detail = description['detail']
                player.role_image = description['image']
                player.save()
            except Exception as e:
                pass
    

    def __str__(self):
        return f"Game Session: {self.session_id}"


class Player(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=50, unique=False)
    pin = models.CharField(max_length=128)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    role = models.CharField(max_length=128, blank=True)
    role_intro  = models.TextField()
    role_detail = models.TextField()
    role_image  = models.TextField()

    @property
    def safe_role_detail(self):
        return mark_safe(self.role_detail)

    class Meta:
        unique_together = ('game_session', 'nickname') # 한 세션 내에서 닉네임 중복 방지

    def __str__(self):
        return f"{self.nickname} in {self.game_session.session_id}"