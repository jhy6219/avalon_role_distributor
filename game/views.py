from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import GameRoom, Player
import json
import random
import string

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def home(request):
    return render(request, 'game/home.html')

def create_room(request):
    if request.method == 'POST':
        host_name = request.POST.get('host_name')
        include_oberon = request.POST.get('include_oberon') == 'on'
        include_mordred = request.POST.get('include_mordred') == 'on'
        
        if not host_name:
            messages.error(request, '호스트 이름을 입력해주세요.')
            return redirect('home')
        
        room_code = generate_room_code()
        while GameRoom.objects.filter(room_code=room_code).exists():
            room_code = generate_room_code()
        
        room = GameRoom.objects.create(
            room_code=room_code,
            host_name=host_name,
            include_oberon=include_oberon,
            include_mordred=include_mordred
        )
        
        Player.objects.create(
            room=room,
            name=host_name,
            is_host=True
        )
        
        request.session['player_name'] = host_name
        request.session['room_code'] = room_code
        
        return redirect('game_room', room_code=room_code)
    
    return redirect('home')

def join_room(request):
    if request.method == 'POST':
        room_code = request.POST.get('room_code').upper()
        player_name = request.POST.get('player_name')
        
        if not room_code or not player_name:
            messages.error(request, '방 코드와 플레이어 이름을 모두 입력해주세요.')
            return redirect('home')
        
        try:
            room = GameRoom.objects.get(room_code=room_code, is_active=True)
        except GameRoom.DoesNotExist:
            messages.error(request, '존재하지 않는 방입니다.')
            return redirect('home')
        
        if Player.objects.filter(room=room, name=player_name).exists():
            messages.error(request, '이미 존재하는 플레이어 이름입니다.')
            return redirect('home')
        
        if room.players.count() >= 10:
            messages.error(request, '방이 가득 찼습니다.')
            return redirect('home')
        
        Player.objects.create(
            room=room,
            name=player_name
        )
        
        request.session['player_name'] = player_name
        request.session['room_code'] = room_code
        
        return redirect('game_room', room_code=room_code)
    
    return redirect('home')

def game_room(request, room_code):
    try:
        room = GameRoom.objects.get(room_code=room_code, is_active=True)
    except GameRoom.DoesNotExist:
        messages.error(request, '존재하지 않는 방입니다.')
        return redirect('home')
    
    player_name = request.session.get('player_name')
    if not player_name:
        messages.error(request, '플레이어 정보가 없습니다.')
        return redirect('home')
    
    try:
        player = Player.objects.get(room=room, name=player_name)
    except Player.DoesNotExist:
        messages.error(request, '플레이어 정보를 찾을 수 없습니다.')
        return redirect('home')
    
    context = {
        'room': room,
        'player': player,
        'players': room.players.all().order_by('joined_at'),
        'game_state': room.get_game_state()
    }
    
    return render(request, 'game/room.html', context)

@csrf_exempt
def start_game(request, room_code):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        room = GameRoom.objects.get(room_code=room_code, is_active=True)
    except GameRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    
    player_name = request.session.get('player_name')
    try:
        player = Player.objects.get(room=room, name=player_name, is_host=True)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Only host can start the game'}, status=403)
    
    players = list(room.players.all())
    player_count = len(players)
    
    if player_count < 5:
        return JsonResponse({'error': '최소 5명의 플레이어가 필요합니다.'}, status=400)
    
    # 역할 배정
    roles = assign_roles(player_count, room.include_oberon, room.include_mordred)
    random.shuffle(roles)
    
    for i, player in enumerate(players):
        player.role = roles[i]
        player.save()
    
    # 게임 상태 초기화
    game_state = {
        'phase': 'role_reveal',
        'round': 1,
        'mission_results': [],
        'current_leader': 0,
        'team_proposal': [],
        'votes': {},
        'mission_votes': {},
        'evil_wins': 0,
        'good_wins': 0
    }
    
    room.set_game_state(game_state)
    
    return JsonResponse({'success': True, 'game_state': game_state})

def assign_roles(player_count, include_oberon, include_mordred):
    # 기본 역할 구성
    role_config = {
        5: {'merlin': 1, 'percival': 1, 'servant': 2, 'assassin': 1, 'minion': 0},
        6: {'merlin': 1, 'percival': 1, 'servant': 2, 'assassin': 1, 'minion': 1},
        7: {'merlin': 1, 'percival': 1, 'servant': 2, 'assassin': 1, 'minion': 2},
        8: {'merlin': 1, 'percival': 1, 'servant': 3, 'assassin': 1, 'minion': 2},
        9: {'merlin': 1, 'percival': 1, 'servant': 4, 'assassin': 1, 'minion': 2},
        10: {'merlin': 1, 'percival': 1, 'servant': 4, 'assassin': 1, 'minion': 3}
    }
    
    config = role_config[player_count].copy()
    
    # 특수 캐릭터 추가
    if include_mordred and config['minion'] > 0:
        config['minion'] -= 1
        config['mordred'] = 1
    
    if include_oberon and config['minion'] > 0:
        config['minion'] -= 1
        config['oberon'] = 1
    
    # 역할 리스트 생성
    roles = []
    for role, count in config.items():
        roles.extend([role] * count)
    
    return roles

@csrf_exempt
def vote(request, room_code):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        room = GameRoom.objects.get(room_code=room_code, is_active=True)
    except GameRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    
    player_name = request.session.get('player_name')
    data = json.loads(request.body)
    vote_type = data.get('vote')  # 'approve' or 'reject'
    
    game_state = room.get_game_state()
    if game_state.get('phase') != 'voting':
        return JsonResponse({'error': 'Not in voting phase'}, status=400)
    
    game_state['votes'][player_name] = vote_type
    room.set_game_state(game_state)
    
    return JsonResponse({'success': True})

@csrf_exempt
def mission_action(request, room_code):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        room = GameRoom.objects.get(room_code=room_code, is_active=True)
    except GameRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    
    player_name = request.session.get('player_name')
    data = json.loads(request.body)
    action = data.get('action')  # 'success' or 'fail'
    
    game_state = room.get_game_state()
    if game_state.get('phase') != 'mission':
        return JsonResponse({'error': 'Not in mission phase'}, status=400)
    
    game_state['mission_votes'][player_name] = action
    room.set_game_state(game_state)
    
    return JsonResponse({'success': True})

@csrf_exempt
def restart_game(request, room_code):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        room = GameRoom.objects.get(room_code=room_code, is_active=True)
    except GameRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    
    player_name = request.session.get('player_name')
    try:
        player = Player.objects.get(room=room, name=player_name, is_host=True)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Only host can restart the game'}, status=403)
    
    # 게임 상태 초기화 (로비로 돌아가기)
    room.players.update(role='', is_ready=False)
    room.set_game_state({})
    
    return JsonResponse({'success': True, 'message': '로비로 돌아갑니다.'})