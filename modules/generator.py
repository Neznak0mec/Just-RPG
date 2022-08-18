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

item = {"_id": None,
        "name": None,
        "lvl": None,
        "type": None,
        "price": None,
        "description": None,
        "rarity": None,
        "give_stats": {
            "hp": 0,
            "damage": 0,
            "defence": 0,
            "luck": 0,
            "speed": 0
        },
        "generated": True
        }
types = ['helmet', 'armor', 'pants', 'shoes', 'gloves', 'weapon']
rarity = ['common', 'uncommon', 'rare', 'epic', 'legendary']


def generate_enemy(bot, name, lvl, url) -> dict:
    lvl += random.randint(1, 3)
    points = lvl * 3
    enemy = mob.copy()
    enemy['name'] = name
    enemy['lvl'] = lvl
    enemy['url'] = url
    enemy['hp'] = 7
    enemy['damage'] = 3
    stats = ['damage', 'hp', 'defence']

    for i in range(points):
        enemy[random.choice(stats)] += 1

    enemy['max_def'] = enemy['defence']
    enemy['max_hp'] = enemy['hp']

    return enemy


# loot generator
def generate_loot(bot, name, lvl, type):
    loot = item.copy()
    loot['name'] = name
    loot['lvl'] = lvl

    return
