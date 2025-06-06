import random

def distributor(player_ids, is_persival, is_morigana):
    player_no = len(player_ids)
    persival_player_no = int(is_persival)
    morigana_player_no = int(is_morigana)

    if player_no < 5 or player_no > 10:
        raise ValueError("player_no must be between 5 and 10")
    
    if player_no <= 6:
        bad_player_no = 2
    elif player_no <= 9:
        bad_player_no = 3
    else:
        bad_player_no = 4

    good_player_no = player_no - bad_player_no
    shuffled = player_ids[:]
    random.shuffle(shuffled)
    slices = {
        "good": (0, good_player_no),
        "merlin": (0, 1),
        "persival": (1, 1 + persival_player_no),
        "bad": (good_player_no, len(shuffled)+1),
        "morigana": (good_player_no, good_player_no + morigana_player_no),
    }

    # ✅ 이 시점에 set으로 반환
    result = {role: set(shuffled[start:end]) for role, (start, end) in slices.items()}
    return result

messages = {
    "good": '''
    🕊️ 당신은 선인입니다. (아서왕의 충성스러운 신하)
    정의와 진실을 위해 함께 힘을 모아 승리를 향해 나아가세요!
    ''',
    "merlin": '''
    🧙‍♂️ 당신은 멀린입니다. 
    악인을 찾아내고 선인들을 지켜야 합니다! 
    악인은 {bad_players} 입니다.
    ''',
    "persival-with-morigana": '''
    🛡️ 당신은 퍼시발입니다. 
    멀린을 보호하고, 그의 정체를 추리해 선인들에게 희망을 주세요! 
    멀린은 {merlin_candidates} 중 한명이고,
    나머지 한명은 악인 모르가나입니다.
    ''',
    "persival-no-morigana": '''
    🛡️ 당신은 퍼시발입니다. 
    멀린을 보호하고 선인들에게 희망을 주세요! 
    멀린은 {merlin} 입니다.
    ''',
    "bad": '''
    🗡️ 당신은 악인입니다. (모드레드의 흉악한 수하)
    선인들을 속이고 혼란을 일으켜 어둠의 승리를 쟁취하세요! 
    함께하는 악인은 {bad_players} 입니다.
    ''',
    "morigana": '''
    🦹‍♀️ 당신은 모르가나입니다. 
    멀린을 위장하고 악의 동료들과 교묘하게 작전을 펼치세요! 
    함께하는 악인은 {bad_players} 입니다.
    '''
}

def generate_player_info(roles, user_info_df):
    user_info = user_info_df.set_index("player_ids").to_dict(orient="index")
    
    id_to_name = user_info_df.set_index('player_ids')['name'].to_dict()
    
    merlin = set(roles.get("merlin", []))
    persival = set(roles.get("persival", []))
    morigana = set(roles.get("morigana", []))
    bad = set(roles.get("bad", []))

    for player in user_info.keys():
        if player in merlin:
            bad_names = ", ".join(id_to_name[p] for p in sorted(bad))
            msg = messages["merlin"].format(bad_players=bad_names)
        elif player in persival:
            if morigana:
                candidates = sorted(merlin | morigana)
                candidate_names = ", ".join(id_to_name[p] for p in candidates)
                msg = messages["persival-with-morigana"].format(merlin_candidates=candidate_names)
            else:
                merlin_player = next(iter(merlin))
                msg = messages["persival-no-morigana"].format(merlin=id_to_name[merlin_player])
        elif player in morigana:
            others = sorted(bad - {player})
            other_names = ", ".join(id_to_name[p] for p in others)
            msg = messages["morigana"].format(bad_players=other_names)
        elif player in bad:
            others = sorted(bad - {player})
            other_names = ", ".join(id_to_name[p] for p in others)
            msg = messages["bad"].format(bad_players=other_names)
        elif player in roles["good"]:
            msg = messages["good"]

        user_info[player]["msg"] = msg

    return user_info
