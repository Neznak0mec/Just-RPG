# enemy generator
import random
import json
import uuid

item = {"_id": None,
        "name": None,
        "lvl": None,
        "type": None,
        "price": None,
        "description": None,
        "rarity": None,
        "preset": None,
        "give_stats": None,
        "generated": True
        }

types = ['helmet', 'armor', 'pants', 'shoes', 'gloves', 'weapon']
rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']

give_stats = {
    "hp": None,
    "damage": None,
    "defence": None,
    "luck": None,
    "speed": None,
    "krit": None
}
main_stats = {
    'helmet': "hp",
    'weapon': "damage",
    'armor': "defence",
    'pants': "luck",
    'shoes': "speed",
    'gloves': "krit"
}


def choose_rarity() -> str:
    if random.randint(1, 10000) == 1:
        return 'legendary'
    elif random.randint(1, 1000) == 1:
        return 'epic'
    elif random.randint(1, 100) == 1:
        return 'rare'
    elif random.randint(1, 10) == 1:
        return 'uncommon'
    else:
        return 'common'


def main_stat(lvl, type, rarity) -> dict:
    stat = give_stats.copy()
    stat[main_stats[type]] = lvl * (rarities.index(rarity)+1) * 2
    return stat


def select_preset(lvl, rarity) -> list[str, dict]:
    mydict = None
    with open('json/presetts.json', 'r', encoding='utf-8') as f:
        mydict = json.load(f)

    preset = random.choice(list(mydict.keys()))
    stats = dict(mydict[preset])
    for i in stats:
        if i == 0:
            continue
        stats[i] *= (rarities.index(rarity) / 2 + 1 * lvl / 10)

    return [preset, stats]


def add_stats(stats_1, stats_2):
    for i in stats_2.keys():
        if stats_1[i] is None:
            stats_1[i] = 0
        stats_1[i] += stats_2[i]
        stats_1[i] = int(stats_1[i])
    return stats_1


# loot generator
def generate_loot(bot, name, lvl, type) -> str:
    rarity = choose_rarity()
    preset = select_preset(lvl, rarity)
    if bot.info_db.count_documents({"name": name, "lvl": lvl, "presset": preset[0]}) != 0:
        loot = bot.info_db.find_one({"name": name, "lvl": lvl, "presset": preset[0]})
        return f"{loot['name']} {loot['preset']}"

    loot = item.copy()
    loot['_id'] = uuid.uuid4()
    loot['name'] = name
    loot['lvl'] = lvl
    loot['type'] = type
    loot['rarity'] = rarity
    loot['preset'] = preset[0]

    loot['give_stats'] = add_stats(main_stat(lvl, type, rarity), preset[1])

    bot.info_db.insert_one(loot)
    return f"{loot['name']} {loot['preset']}"
