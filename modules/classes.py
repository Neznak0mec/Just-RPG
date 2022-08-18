import random

import discord


class beings:
    def __init__(self):
        self.hp = 0
        self.damage = 0
        self.defence = 0
        self.max_def = None
        self.max_hp = None
        self.speed = 0
        self.luck = 0
        self.krit = 0

    def get_damage(self, damage: int) -> float:
        proc = round(damage / 5 * 100)
        damage += random.randint(-proc, proc) / 100


        if self.defence > 0:
            self.defence -= damage
            if self.defence < 0:
                self.hp += self.defence
                self.defence = 0
        else:
            self.hp -= damage

        if self.hp < 0:
            self.hp = 0

        return damage

    def add_stats(self, stat, much) -> None:
        if stat == 'hp':
            self.hp += much
        elif stat == 'damage':
            self.damage += much
        elif stat == 'defence':
            self.defence += much
        elif stat == 'speed':
            self.speed += much
        elif stat == 'luck':
            self.luck += much
        elif stat == 'krit':
            self.krit += much

    def hp_bar(self) -> str:
        if self.hp != 0:
            proc = self.hp / self.max_hp * 100
            return "[" + "█" * int(proc / 10 - 1) + (lambda: "█" if int(proc) % 10 >= 5 else "▒")() + "-" * (
                    10 - int(proc / 10) - 1) + "]" + f" {self.hp:.2f}/{self.max_hp}"

        return "[" + "-" * 10 + "]" + f" {self.hp:.2f}/{self.max_hp}"

    def defence_bar(self) -> str:
        if self.defence != 0:
            proc = self.defence / self.max_def * 100
            return "[" + "█" * int(proc / 10 - 1) + (lambda: "█" if int(proc) % 10 >= 5 else "▒")() + "-" * (
                    10 - int(proc / 10) - 1) + "]" + f" {self.defence:.2f}/{self.max_def}"

        return "[" + "-" * 10 + "]" + f" {self.defence:.2f}/{self.max_def}"


class Enemy(beings):
    def __init__(self, name, lvl, url):
        super().__init__()
        self.lvl = lvl + random.randint(1, 3)
        self.name = name
        self.url = url
        self.hp = 10
        self.damage = 3

        self.gen_stats()

    def gen_stats(self) -> None:
        points = self.lvl * 3
        for i in range(points):
            self.add_stats(random.choice(['hp', 'damage', 'defence']), 1)

        self.max_def = self.defence
        self.max_hp = self.hp


class Player(beings):
    def __init__(self, pl : discord.User, bot):
        super().__init__()
        user = bot.users_db.find_one({"_id": pl.id})
        self.bot = bot

        self.id = pl.id
        self.name = pl.name
        self.lvl = user['lvl']
        self.hp = user['hp']
        self.damage = user['damage']
        self.defence = user['defence']
        self.max_def = None
        self.max_hp = None
        self.speed = user['speed']
        self.luck = user['luck']
        self.krit = user['krit']
        self.inventory = user['inventory']
        self.equipment = user['equipment']

        self.gen_stats()

    def gen_stats(self) -> None:
        for i in self.equipment.keys():
            sel = self.equipment[i]
            if sel is None:
                continue

            item = self.bot.items_db.find_one({"_id": sel})
            for f in item['give_stats'].keys():
                self.add_stats(f, item['give_stats'][f])

        self.max_def = self.defence
        self.max_hp = self.hp

    def rem_heal(self) -> bool:
        HEAL_POTION_ID = "fb75ff73-1116-4e95-ae46-8075c4e9a782"

        if HEAL_POTION_ID in self.inventory:
            self.inventory.remove(HEAL_POTION_ID)
            self.hp += self.max_hp / 4
            if self.hp > self.max_hp:
                self.hp = self.max_hp

            temp = self.bot.users_db.find_one({"_id": self.id})['inventory']
            temp.remove(HEAL_POTION_ID)

            self.bot.users_db.update_one({"_id": self.id}, {"$set": {"inventory": temp}})
            return True

        return False
