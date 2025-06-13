import json
import hashlib

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpRequest, HttpResponseRedirect, HttpResponseNotAllowed, JsonResponse
from django.urls import reverse
from urllib.parse import urlencode
from .models import GameSession, Player


def home(request:HttpRequest):
    if request.method == 'POST':
        op1 = request.POST.get('option1') == 'true'
        op2 = request.POST.get('option2') == 'true'
        op3 = request.POST.get('option3') == 'true'
        game_session = GameSession.objects.create(
            option1=op1,
            option2=op2,
            option3=op3
        )

        game_session.is_active = True
        game_session.save()

        return redirect('join', session_id=game_session.session_id)
    
    return render(request, 'game/home.html')


def join(request:HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)

    if not game_session.is_active:
        return render(request, 'game/ended.html', {
            'message': '이 게임 세션은 종료되었습니다.',
            'game_session': game_session,
            'players_in_session': game_session.players.all(),
        })
    
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        pin = request.POST.get('pin')

        if not nickname or not pin:
            return render(request, 'game/join.html', {
                'game_session': game_session,
                'message_text': '닉네임과 비밀번호를 모두 입력해주세요.',
                'message_level': 'error',
            })

        try:
            player = Player.objects.get(game_session=game_session, nickname=nickname)
            if not check_password(pin, player.pin):
                return render(request, 'game/join.html', {
                    'game_session': game_session,
                    'message_text': '비밀번호가 틀렸습니다.',
                    'message_level': 'error',
                })
        except Player.DoesNotExist:
            if game_session.is_started:
                return render(request, 'game/join.html', {
                    'game_session': game_session,
                    'message_text': '이미 시작된 게임입니다.',
                    'message_level': 'error',
                })
            
            hashed_pin = make_password(pin)
            Player.objects.create(
                game_session=game_session,
                nickname=nickname,
                pin=hashed_pin
            )

             # 호스트가 비어 있다면 첫 참가자로 지정
            if not game_session.host_nickname:
                game_session.host_nickname = nickname
                game_session.save()

        # redirect 방식 적용 (PRG)
        query = urlencode({'nickname': nickname, 'pin': pin})
        return HttpResponseRedirect(f"{reverse('lobby', args=[session_id])}?{query}")

    return render(request, 'game/join.html', {'game_session': game_session})


def lobby(request:HttpRequest, session_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    game_session = get_object_or_404(GameSession, session_id=session_id)

    # 종료된 세션일 경우 입장 불가
    if not game_session.is_active:
        return render(request, 'game/ended.html', {
            'message': '이 게임 세션은 종료되었습니다.',
            'game_session': game_session,
            'players_in_session': game_session.players.all(),
        })

    nickname = request.GET.get('nickname')
    pin = request.GET.get('pin')

    if not nickname or not pin:
        return redirect('join', session_id=session_id)

    try:
        player = Player.objects.get(game_session=game_session, nickname=nickname)
        if not check_password(pin, player.pin):
            return redirect('join', session_id=session_id)
        
    except Player.DoesNotExist:
        return render(request, 'game/kicked.html', {
            'message': '이 세션에서 퇴장당했거나 존재하지 않는 사용자입니다.',
            'game_session': game_session,
        })

    return render(request, 'game/lobby.html', {
        'game_session': game_session,
        'player_nickname': nickname,
        'player_pin': pin,
        'players_in_session': game_session.players.all(),
        'session_link': request.build_absolute_uri(reverse('join', args=[session_id])),
        'host_nickname': game_session.host_nickname,
    })


def start_game(request:HttpRequest, session_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    game_session = get_object_or_404(GameSession, session_id=session_id)
    nickname = request.POST.get('nickname') # 게임 시작 요청자 (호스트여야 함)
    pin = request.POST.get('pin')

    if nickname != game_session.host_nickname:
        return JsonResponse({'status': 'error', 'message': '게임 시작 권한이 없습니다.'}, status=403)

    try:
        host_player = Player.objects.get(game_session=game_session, nickname=nickname)
        if not check_password(pin, host_player.pin):
            return JsonResponse({'status': 'error', 'message': '인증 실패.'}, status=401)
    except Player.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '호스트 정보를 찾을 수 없습니다.'}, status=404)


    # 역할 분배
    game_session.distribute_roles()

    game_session.is_started = True
    game_session.save()

    query = urlencode({'nickname': nickname, 'pin': pin})
    return HttpResponseRedirect(f"{reverse('role', args=[session_id])}?{query}")


def role(request:HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)
    
    if not game_session.is_active:
        return render(request, 'game/ended.html', {
            'message': '이 게임 세션은 종료되었습니다.',
            'game_session': game_session,
            'players_in_session': game_session.players.all(),
        })

    if not game_session.is_started:
        return redirect('lobby', session_id=session_id)

    player_nickname = request.GET.get('nickname')
    player_pin = request.GET.get('pin')

    if not player_nickname or not player_pin:
        return redirect('join', session_id=session_id)

    try:
        player = Player.objects.get(game_session=game_session, nickname=player_nickname)
        if not check_password(player_pin, player.pin):
            return redirect('join', session_id=session_id)
    except Player.DoesNotExist:
        return render(request, 'game/kicked.html', {
            'message': '이 세션에 참가하지 않았거나 존재하지 않는 사용자입니다.',
            'game_session': game_session,
        })


    return render(request, 'game/role.html', {
        'game_session': game_session,
        'player_nickname': player_nickname,
        'player_pin': player_pin,
        'players_in_session': game_session.players.all(),
        'host_nickname': game_session.host_nickname,
        'player': player,
        'role_detail': player.safe_role_detail
    })



def end_game(request:HttpRequest, session_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    game_session = get_object_or_404(GameSession, session_id=session_id)

    if not game_session.is_active:
        return JsonResponse({'status': 'error', 'message': '이미 종료된 게임입니다.'}, status=400)


    nickname = request.POST.get('nickname') 
    pin = request.POST.get('pin')

    if nickname != game_session.host_nickname:
        return JsonResponse({'status': 'error', 'message': '게임 종료 권한이 없습니다.'}, status=403)
    
    try:
        host_player = Player.objects.get(game_session=game_session, nickname=nickname)
        if not check_password(pin, host_player.pin):
            return JsonResponse({'status': 'error', 'message': '인증 실패.'}, status=401)
    except Player.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '호스트 정보를 찾을 수 없습니다.'}, status=404)


    game_session.is_active = False  
    game_session.save()

    return redirect('ended', session_id=session_id)


def ended(request:HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)
    return render(request, 'game/ended.html', {
            'message': f'세션 {session_id}은(는) 종료되었습니다.',
            'game_session': game_session,
            'players_in_session': game_session.players.all(),
        })


def get_state(request:HttpRequest, session_id):
    game_session = get_object_or_404(GameSession, session_id=session_id)

    if not game_session.is_active:
        return JsonResponse({'players': []})

    player_names = list(game_session.players.all().values_list('nickname', flat=True))
    is_started = game_session.is_started

    # 게임 상태 해시 생성
    data_to_hash = {
        'players': player_names,
        'is_started': is_started
    }
    state_hash = hashlib.md5(json.dumps(data_to_hash).encode()).hexdigest()
    client_hash = request.GET.get('hash')

    if client_hash and client_hash == state_hash and not is_started:
        return JsonResponse({}, status=204)  # 변경 없음

    return JsonResponse({
        'players': player_names,
        'host_nickname': game_session.host_nickname,
        'hash': state_hash,
        'is_active': game_session.is_active,
        'is_started': game_session.is_started,
    })


def kick_player(request:HttpRequest, session_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    game_session = get_object_or_404(GameSession, session_id=session_id)
    target_nickname = request.POST.get('target_nickname')
    kicker_nickname = request.POST.get('nickname')
    kicker_pin = request.POST.get('pin')

    if not game_session.is_active:
        return render(request, 'game/ended.html', {'message': '종료된 세션입니다.'})

    if game_session.is_started:
        return JsonResponse({'status': 'error', 'message': '게임이 시작되어 참가자를 추방할 수 없습니다.'}, status=400)

    if target_nickname == kicker_nickname:
        return render(request, 'game/kicked.html', {
            'message': '자기 자신은 제거할 수 없습니다.',
            'game_session': game_session,
        })

    if kicker_nickname != game_session.host_nickname:
        return render(request, 'game/kicked.html', {
            'message': '관리자만 참가자를 제거할 수 있습니다.',
        })

    try:
        target = Player.objects.get(game_session=game_session, nickname=target_nickname)
        target.delete()
    except Player.DoesNotExist:
        pass

    query = urlencode({'nickname': kicker_nickname, 'pin': kicker_pin})
    return redirect(f"{reverse('lobby', args=[session_id])}?{query}")