# game/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import GameSession, Player
from django.contrib import messages
from django.contrib.sessions.models import Session
import hashlib # 비밀번호 해싱을 위한 라이브러리 (실제로는 Django의 auth 모듈 사용 권장)

# 간단한 비밀번호 해싱 함수 (실제 사용 시에는 Django의 make_password 등을 사용하세요)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def home(request):
    return render(request, 'game/home.html')

def create_session(request):
    if request.method == 'POST':
        game_session = GameSession.objects.create()
        # 세션이 생성되면, 호스트에게 해당 세션의 링크를 보여주고,
        # 호스트 정보를 세션에 저장 (선택 사항)
        request.session['host_session_id'] = str(game_session.session_id)
        return redirect('join_session', session_id=game_session.session_id)
    return render(request, 'game/create_session.html')

def join_session(request, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)

    # 이미 플레이어로 참여 중인지 확인 (세션 기반)
    player_id = request.session.get('player_id')
    if player_id:
        try:
            player = Player.objects.get(id=player_id, game_session=game_session)
            # 이미 참여 중이고 유효한 플레이어라면 바로 로비로 이동
            if player.session_key == request.session.session_key:
                messages.info(request, f"환영합니다, {player.nickname}님! 게임에 다시 참여하셨습니다.")
                return redirect('game_lobby', session_id=session_id)
        except Player.DoesNotExist:
            pass # 플레이어는 있지만 현재 세션에 속하지 않거나, session_key가 다르면 새로 참여하도록

    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        password = request.POST.get('password')

        if not nickname or not password:
            messages.error(request, "닉네임과 비밀번호를 모두 입력해주세요.")
            return render(request, 'game/join_session.html', {'game_session': game_session})

        # 닉네임 중복 확인 (해당 세션 내에서)
        if Player.objects.filter(game_session=game_session, nickname=nickname).exists():
            messages.error(request, "이미 사용 중인 닉네임입니다. 다른 닉네임을 사용해주세요.")
            return render(request, 'game/join_session.html', {'game_session': game_session})

        # 플레이어 생성 및 세션에 저장
        hashed_password = hash_password(password) # 실제로는 Django의 make_password 사용
        player = Player.objects.create(
            game_session=game_session,
            nickname=nickname,
            password=hashed_password,
            session_key=request.session.session_key # 현재 세션 키 저장
        )
        request.session['player_id'] = player.id
        request.session['nickname'] = nickname
        messages.success(request, f"{nickname}님, 게임에 참여하셨습니다!")
        return redirect('game_lobby', session_id=session_id)
    return render(request, 'game/join_session.html', {'game_session': game_session})

def game_lobby(request, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)
    
    # 세션에서 플레이어 ID 가져오기
    player_id = request.session.get('player_id')
    player = None
    if player_id:
        try:
            player = Player.objects.get(id=player_id, game_session=game_session)
            # 세션 키가 일치하는지 확인하여 재접속 유효성 검사
            if player.session_key != request.session.session_key:
                player = None # 세션 키가 다르면 무효화
        except Player.DoesNotExist:
            player = None

    if not player:
        messages.error(request, "세션에 참여해야 게임 로비에 접속할 수 있습니다.")
        return redirect('join_session', session_id=session_id)

    # 해당 세션에 참여한 모든 플레이어 목록 가져오기
    players_in_session = game_session.players.all()
    
    # 세션 공유 링크
    session_link = request.build_absolute_uri(reverse('join_session', args=[session_id]))

    return render(request, 'game/game_lobby.html', {
        'game_session': game_session,
        'player': player,
        'players_in_session': players_in_session,
        'session_link': session_link,
    })