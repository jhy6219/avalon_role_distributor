from ftn.generate_msg import distributor, distribution_post_process




players = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

raw = distributor(players, True, True)
res = distribution_post_process(raw)

for p, des in res.items():
    print(f'{p}: {des['role']}')
    print(f'{des['intro']}')
    print(f'{des['detail']}')
    print(f'{des['image']}')
    print()
