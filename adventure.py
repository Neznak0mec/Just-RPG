import discord
import pymongo
from discord import app_commands
from discord.ext import commands
import random

import checker
from profiler import lvl_up

connection = ""
cluster = pymongo.MongoClient(connection)

db = cluster["MMORPG"]

users_db = db["users"]
servers_db = db["servers"]
info_db = db["info"]
item_db = db["items"]


def dmg_randomer(dmg):
    proc = dmg / 5 * 100

    return random.randint(int(-proc), int(proc)) / 100


def stats_calc(player):
    us = users_db.find_one({"_id": player.id})

    stats = {'heal': us['heal'],
             'damage': us['damage'],
             'defence': us['defence'],
             'max_def': us['defence'],
             'max_hp': us['heal'],
             'speed': us['speed'],
             'luck': us['luck'],
             'krit': us['krit'],
             'lvl': us['lvl'],
             'items': us['inventory']}

    for i in us['equipment'].keys():
        sel = us['equipment'][i]
        if sel is None:
            continue

        item = item_db.find_one({"_id": sel})
        for f in item['give_stats'].keys():
            stats[f] += item['give_stats'][f]

    stats['max_def'] = stats['defence']
    stats['max_hp'] = stats['heal']

    return stats


class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)
    @app_commands.command(name="adventure", description="Отправится в небольшой поход")
    async def dungeon(self, interaction: discord.Interaction):
        await checker.check(interaction)
        view = discord.ui.View(timeout=180).add_item(Select_dangeon(interaction))
        emb = discord.Embed(title=f'Выберите куда хочешь отправиться',
                            description=f'Поход - самый эффективный способ прокачки для новичков.')
        # await interaction.response.send_message(embed=emb, view=view, ephemeral=True)
        await interaction.response.send_message(embed=emb, view=view)


class Select_dangeon(discord.ui.Select):
    def __init__(self, ctx: discord.Interaction):
        options = []

        dan = info_db.find_one({"_id": "locations"})['loks']

        for i in dan:
            options.append(discord.SelectOption(label=f"{i['name']} - {i['lvl']}", description=i['description']))

        self.author = ctx.user
        self.stats = stats_calc(ctx.user)

        super().__init__(placeholder='Выбери локацию для битвы с монстром', min_values=1, max_values=1,
                         options=options)


    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=checker.err_embed(
                f"Это не вы собираетесь в путешествие"), ephemeral=True)
            return
        dan = info_db.find_one({"_id": "locations"})['loks']

        for i in dan:
            if self.values[0].startswith(i['name']):
                dan = i
                break

        lvl = random.randint(dan['lvl'], dan['lvl'] + 4)
        hp_gen = random.randint(dan['lvl'] * 7, lvl * random.randint(8, 12))
        mob = {
            "name": random.choice(dan['monsters']),
            "lvl": lvl,
            "heal": hp_gen,
            "max_hp": hp_gen,
            "defence": 0,
            "max_def": 0,
            "damage": random.randint(dan['lvl'] * 3, lvl * random.randint(4, 5)),
        }

        mob['url'] = dan['urls'][mob['name']]

        emb = game_emb(self.stats, mob)

        view = Dangeon(self.author, self.stats, mob, dan['drop'], interaction)

        await interaction.response.edit_message(embed=emb, view=view)


def hp_calc(stats):
    proc = stats['heal'] / stats['max_hp'] * 100
    return "[" + "█" * int(proc / 10 - 1) + (lambda: "█" if int(proc) % 10 >= 5 else "▒")() + "-" * (
            10 - int(proc / 10) - 1) + "]" + f" {stats['heal']:.2f}/{stats['max_hp']}"


def def_calc(oba):
    proc = oba['defence'] / oba['max_def'] * 100
    return "[" + "█" * int(proc / 10 - 1) + (lambda: "█" if int(proc) % 10 >= 5 else "▒")() + "-" * (
            10 - int(proc / 10) - 1) + "]" + f" {oba['defence']:.2f}/{oba['max_def']}"


def game_emb(stats, mob, log=None):
    emb = discord.Embed(title=f"Битва с {mob['name']} - {mob['lvl']}", description="\u200b")
    emb.add_field(name=f"Вы - {stats['lvl']}", value=f"hp - {hp_calc(stats)}\n"
                                                     f"броня - {def_calc(stats)}\n"
                                                     f"урон - {stats['damage']}")

    emb.add_field(name=f"{mob['name']} - {mob['lvl']}", value=f"hp - {hp_calc(mob)}\n"
                                                              f"урон - {mob['damage']}", inline=False)

    if log is not None:
        emb.add_field(name="Лог", value=log, inline=False)

    emb.set_thumbnail(url=mob['url'])

    return emb


def game_loose(mob, log, author):
    loss_cash = int(users_db.find_one({"_id": author.id})['cash'] / 5)
    loss_exp = int(users_db.find_one({"_id": author.id})['exp'] / 5)

    users_db.update_one({"_id": author.id}, {"$inc": {"cash": -loss_cash, "exp": -loss_exp}})

    log += f"Вы проиграли и потеряли {loss_cash} монет и {loss_exp} опыта\n"

    emb = discord.Embed(title=f"Проигрыш", description="\u200b")
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob['url'])

    return emb


def game_win(mob, log, stats, author, drop):
    exp = random.randint(mob['lvl'] * 3, mob['lvl'] * 5)
    coins = mob['lvl'] * 3 + random.randint(0, 7 * stats['luck'])

    users_db.update_many({"_id": author.id}, {"$inc": {"exp": exp, "cash": coins}})

    if drop is not None:
        for b in drop.keys():
            if random.randint(1, drop[b]) == 1:
                item = item_db.find_one({"_id": b})
                log += f"Вы выбили {item['name']}\n"
                users_db.update_one({"_id": author.id}, {"$push": {"inventory": item['_id']}})

    log += f"Вы победили\nВ качестве награды вы получили exp - {exp} и монет - {coins}\n"

    emb = discord.Embed(title=f"Победа", description="\u200b")
    if lvl_up(author):
        log += f"Вы получили новый уровень\n"
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob['url'])

    return emb


def game_run(mob, log, author):
    if random.randint(1, 5) == 1:
        cash = users_db.find_one({"_id": author.id})['cash']
        cash -= int(cash / 100 * 5)
        users_db.update_many({"_id": author.id}, {"$set": {"cash": cash}})
        log += f"В попыхах вы обранили {int(cash / 100 * 5)} монет\n"

    emb = discord.Embed(title=f"Побег", description="\u200b")
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob['url'])

    return emb


class Dangeon(discord.ui.View):
    def __init__(self, author, stats, mob, drop, iteration):
        super().__init__()
        self.drop = drop
        self.author = author
        self.stats = stats
        self.mob = mob
        self.max_hp = self.stats['heal']
        self.interaction = iteration
        self.game_end = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.interaction = interaction

        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=checker.err_embed(
                f"Вы не участвуете в данном походе"), ephemeral=True)

        return interaction.user.id == self.author.id

    def fight(self, atk, def_):
        if def_['defence'] is not None and def_['defence'] > 0:
            def_['defence'] -= atk
            if def_['defence'] < 0:
                def_['heal'] += def_['defence']
                def_['defence'] = 0
        else:
            def_['heal'] -= atk

    @discord.ui.button(label="Атаковать", style=discord.ButtonStyle.grey, emoji="⚔️")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):

        log = ""

        dmg_bonus = dmg_randomer(int(self.stats['damage']))

        if random.randint(1, 100) < 1 + self.stats['krit']:
            self.fight(self.stats['damage'] * 2 + dmg_bonus, self.mob)
            log += f"Вы нанесли критический удар, тем самым нанеся {self.stats['damage'] * 2 + dmg_bonus:.2f} урона\n"
        else:
            self.fight(self.stats['damage'] + dmg_bonus, self.mob)
            log += f"Вы нанесли {self.stats['damage'] + dmg_bonus:.2f} урона\n"

        dmg_bonus = dmg_randomer(self.mob['damage'])

        if self.mob['heal'] > 0:

            if random.randint(1, 100 - self.stats['speed']) != 1:
                self.fight(self.mob['damage'] + dmg_bonus, self.stats)
                log += f"Монстр нанес вам  {self.mob['damage'] + dmg_bonus:.2f} урона\n"

            else:
                log += "Вы укланились от атаки\n"

            if self.stats['heal'] <= 0:
                self.attack.disabled = True
                self.run.disabled = True
                self.hp.disabled = True

                await self.stop()

                await interaction.response.edit_message(embed=game_loose(self.mob, log, self.author),
                                                        view=self)

                return

            emb = game_emb(self.stats, self.mob, log)

        else:
            if len(interaction.message.embeds[0].fields) != 0:
                for i in range(len(interaction.message.embeds[0].fields)):
                    interaction.message.embeds[0].remove_field(0)

            emb = game_win(self.mob, log, self.stats, self.author, self.drop)

            await self.stop()

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Востановление", style=discord.ButtonStyle.grey, emoji="💚")
    async def hp(self, interaction: discord.Interaction, button: discord.ui.Button):

        log = ""

        for i in self.stats['items']:
            if i['_id'] == 'fb75ff73-1116-4e95-ae46-8075c4e9a782':

                self.stats['heal'] += self.max_hp / 4
                if self.stats['heal'] > self.max_hp:
                    self.stats['heal'] = self.max_hp

                self.stats['items'].remove(i)
                # remove item from user's inventory
                temp = users_db.find_one({"_id": self.author.id})['inventory']
                for r in temp:
                    if r == 'fb75ff73-1116-4e95-ae46-8075c4e9a782':
                        temp.remove(r)
                        users_db.update_one({"_id": self.author.id}, {"$set": {"inventory": temp}})

                log += f"Вы востановили {self.max_hp / 4} хп\n"

                if random.randint(1, 4) == 1:
                    dmg_bonus = dmg_randomer(self.mob['damage'])
                    self.fight(self.mob['damage'] + dmg_bonus, self.stats)
                    log += f"Притивнику удалось нанести вам {self.mob['damage'] + dmg_bonus:.2f} урона\n"

                    if self.stats['heal'] <= 0:
                        await self.stop()

                        await interaction.response.edit_message(
                            embed=game_loose(self.mob, log, self.author), view=self)



                else:
                    log += "Притивнику не удалось ударить вас\n"

                self.interaction = await interaction.response.edit_message(embed=game_emb(self.stats, self.mob, log),
                                                                           view=self)

                return

        log += "У вас нет зелья жизни\n"

        if random.randint(1, 4) != 1:
            dmg_bonus = dmg_randomer(self.mob['damage'])
            self.fight(self.mob['damage'] + dmg_bonus, self.stats)
            log += f"Пока вы лазили по сумке, противник нанёс {self.mob['damage'] + dmg_bonus:.2f} урона\n"

            if self.stats['heal'] <= 0:
                await self.stop()
                await interaction.response.edit_message(embed=game_loose(self.mob, log, self.author),
                                                        view=self)

                return

        else:
            log += "Противнику не удалось ударить вас\n"

        emb = game_emb(self.stats, self.mob, log)

        self.interaction = await interaction.response.edit_message(embed=emb, view=self)
        return

    @discord.ui.button(label="Убежать", style=discord.ButtonStyle.grey, emoji="🚪")
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.interaction = interaction

        if 1 < random.randint(1, 100) < 25 + self.stats['luck']:
            self.attack.disabled = True
            self.run.disabled = True
            self.hp.disabled = True

            log = "Вам удалось спастись\n"
            await self.stop()

            self.interaction = await interaction.response.edit_message(embed=game_run(self.mob, log, self.author),
                                                                       view=self)
            return


        else:
            if random.randint(1, 3) == 1:
                dmg_bonus = + dmg_randomer(self.mob['damage'])
                self.fight(self.mob['damage'] * 2 + dmg_bonus, self.stats)

                log = f"Пока вы пытались убежать противник ударил вас в спину, нанеся {self.mob['damage'] * 2 + dmg_bonus:.2f} урона\n"

            else:
                dmg_bonus = + dmg_randomer(self.mob['damage'])
                self.fight(self.mob['damage'] + dmg_bonus, self.stats)
                log = f"Вам не удалось сбежать, враг нанёс вам {self.mob['damage'] + dmg_bonus:.2f} урона\n"

            if self.stats['heal'] <= 0:
                log += "Вы погибли\n"

                await self.stop()
                await interaction.response.edit_message(embed=game_loose(self.mob, log, self.author),
                                                        view=self)

                return

            self.interaction = self.interaction = await interaction.response.edit_message(
                embed=game_emb(self.stats, self.mob, log))

    async def on_timeout(self) -> None:
        if self.game_end:
            return

        self.attack.disabled = True
        self.run.disabled = True
        self.hp.disabled = True

        loss_cash = int(users_db.find_one({"_id": self.author.id})['cash'] / 100 * 20)
        loss_exp = int(users_db.find_one({"_id": self.author.id})['exp'] / 100 * 20)

        users_db.update_one({"_id": self.author.id}, {"$inc": {"cash": -loss_cash, "exp": -loss_exp}})

        if self.interaction is None:
            return

        if len(self.interaction.message.embeds[0].fields) != 0:
            for i in range(len(self.interaction.message.embeds[0].fields)):
                self.interaction.message.embeds[0].remove_field(0)

        log = f"Пока вы бездействовали противник напал и убил вас. Вы потеряли {loss_cash} монет и {loss_exp} опыта\n"

        emb = discord.Embed(title=f"Время вышло, вы проиграли", description="\u200b")
        emb.add_field(name="Логи", value=log, inline=False)
        emb.set_thumbnail(url=self.mob['url'])

        try:
            await self.interaction.message.edit(embed=emb, view=self)
        except:
            pass

    async def stop(self) -> None:
        self.attack.disabled = True
        self.run.disabled = True
        self.hp.disabled = True

        self.game_end = True

        return

    async def on_error(self, interaction, error: Exception, item) -> None:
        if isinstance(error, TimeoutError):
            await self.on_timeout()
        else:
            raise error



