# game/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpRequest
from .models import GameSession, Player
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import make_password, check_password


def home(request:HttpRequest):
    if request.method == 'POST':
        game_session = GameSession.objects.create()
        request.session['host_session_id'] = str(game_session.session_id)
        return redirect('join', session_id=game_session.session_id)
    return render(request, 'game/home.html')


def join(request: HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)

    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        password = request.POST.get('password')

        if not nickname or not password:
            messages.error(request, "닉네임과 비밀번호를 모두 입력해주세요.")
            return render(request, 'game/join.html', {'game_session': game_session})

        try:
            # 같은 닉네임이 있는 경우: 비밀번호 검증
            player = Player.objects.get(game_session=game_session, nickname=nickname)
            if not check_password(password, player.password):
                messages.error(request, "비밀번호가 틀렸습니다.")
                return render(request, 'game/join.html', {'game_session': game_session})

            # 인증 성공
            request.session['player_id'] = player.id
            request.session['nickname'] = player.nickname
            messages.success(request, f"{nickname}님, 다시 오신 것을 환영합니다!")
            return redirect('lobby', session_id=session_id)

        except Player.DoesNotExist:
            # 새 플레이어 생성
            hashed_password = make_password(password)
            player = Player.objects.create(
                game_session=game_session,
                nickname=nickname,
                password=hashed_password,
                session_key=request.session.session_key
            )
            request.session['player_id'] = player.id
            request.session['nickname'] = nickname
            messages.success(request, f"{nickname}님, 게임에 참여하셨습니다!")
            return redirect('lobby', session_id=session_id)

    return render(request, 'game/join.html', {'game_session': game_session})


def lobby(request:HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)
    
    # 세션에서 플레이어 ID 가져오기
    player_id = request.session.get('player_id')
    player = None
    if player_id:
        try:
            player = Player.objects.get(id=player_id, game_session=game_session)
        except Player.DoesNotExist:
            player = None

    if not player:
        messages.error(request, "세션에 참여해야 게임 로비에 접속할 수 있습니다.")
        return redirect('join', session_id=session_id)

    # 해당 세션에 참여한 모든 플레이어 목록 가져오기
    players_in_session = game_session.players.all()
    
    # 세션 공유 링크
    session_link = request.build_absolute_uri(reverse('join', args=[session_id]))

    return render(request, 'game/lobby.html', {
        'game_session': game_session,
        'player': player,
        'players_in_session': players_in_session,
        'session_link': session_link,
    })