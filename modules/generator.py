# enemy generator
import random

mob = {
    "name": None,
    "lvl": None,
    'hp': 0,
    'damage': 0,
    'defence': 0,
    'max_def': None,
    'max_hp': None,
    'speed': 0,
    'luck': 0,
    'krit': 0,
    "url": None
}


async def generate_enemy(bot, name, lvl, url):
    points = lvl * 3
    enemy = mob.copy()
    enemy['name'] = name
    enemy['lvl'] = lvl
    enemy['url'] = url
    enemy['hp'] = 7
    enemy['damage'] = 3
    stats = ['damage', 'hp', 'defence']

    while points > 0:
        stat = random.choice(stats)
        enemy[stat] += 1
        points -= 1

    enemy['max_def'] = enemy['defence']
    enemy['max_hp'] = enemy['hp']

    return enemy


# loot generator
