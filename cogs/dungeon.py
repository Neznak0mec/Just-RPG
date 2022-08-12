import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.adventure import dmg_randomer, stats_calc, game_emb


class Dun(discord.ui.View):
    def __init__(self, bot, author, interaction, enemy, us_stats):
        super().__init__()
        self.bot = bot
        self.stats = us_stats
        self.author = author
        self.interaction = interaction
        self.enemies = enemy
        self.curr = 0
        self.game_end = False
        self.inventory = self.bot.users_db.find_one({"id": self.author.id})['inventory']
        self.upd_select()

    def upd_select(self):
        self.select.options = []
        self.select.add_option(label="1 - " + self.enemies[0]['name'], description=
        f"{self.enemies[0]['heal'] / self.enemies[0]['max_hp'] * 100:.2f}", emoji="❤️",
                               value="0")

        self.select.add_option(label="2 - " + self.enemies[1]['name'], description=
        f"{self.enemies[1]['heal'] / self.enemies[1]['max_hp'] * 100:.2f}", emoji="❤️"
                               , value="1")
        self.select.add_option(label="3 - " + self.enemies[2]['name'], description=
        f"{self.enemies[2]['heal'] / self.enemies[2]['max_hp'] * 100:.2f}", emoji="❤️"
                               , value="2")

        for i in self.enemies:
            if i['heal'] == 0:
                self.select.options[self.enemies.index(i)].emoji = "☠️"
            if self.enemies.index(i) == self.curr:
                self.select.options[self.enemies.index(i)].emoji = "⚔️"

    def fight(self, atk, def_):
        if def_['defence'] is not None and def_['defence'] > 0:
            def_['defence'] -= atk
            if def_['defence'] < 0:
                def_['heal'] += def_['defence']
                def_['defence'] = 0
        else:
            def_['heal'] -= atk

    @discord.ui.select(options=[], row=0, placeholder="Выберите противника")
    async def select(self, interaction: discord.Interaction, options):
        self.select.disabled = True
        self.curr = int(interaction.data["values"][0])
        self.upd_select()

        emb = game_emb(self.stats, self.enemies[self.curr])
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Атаковать", style=discord.ButtonStyle.grey, emoji="⚔️", row=1)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False

        log = ""

        dmg_bonus = dmg_randomer(int(self.stats['damage']))

        if random.randint(1, 100) < 1 + self.stats['krit']:
            self.fight(self.stats['damage'] * 2 + dmg_bonus, self.enemies[self.curr])
            log += f"Вы нанесли критический удар, тем самым нанеся {self.stats['damage'] * 2 + dmg_bonus:.2f} урона\n"
        else:
            self.fight(self.stats['damage'] + dmg_bonus, self.enemies[self.curr])
            log += f"Вы нанесли {self.stats['damage'] + dmg_bonus:.2f} урона\n"

        dead = [False, False, False]
        for i in self.enemies:
            if i['heal'] <= 0:
                if i['heal'] < 0:
                    i['heal'] = 0
                dead[self.enemies.index(i)] = True

        if any(dead):
            for i in self.enemies:

                if i['heal'] > 0:

                    dmg_bonus = dmg_randomer(i['damage'])

                    if random.randint(1, 100) != 1 + self.stats['speed']:
                        self.fight(i['damage'] + dmg_bonus, self.stats)
                        log += f"Монстр {self.enemies.index(i) + 1} - {i['name']} нанес вам  {i['damage'] + dmg_bonus:.2f} урона\n"

                    else:
                        log += "Вы укланились от атаки\n"

                    if self.stats['heal'] <= 0:
                        self.attack.disabled = True
                        self.run.disabled = True
                        self.hp.disabled = True

                        await self.stop()

                        await interaction.response.edit_message(
                            embed=game_loose(self.enemies[self.curr], log, self.author),
                            view=self)

                        return

            emb = game_emb(self.stats, self.enemies[self.curr], log)

        else:
            if len(interaction.message.embeds[0].fields) != 0:
                for i in range(len(interaction.message.embeds[0].fields)):
                    interaction.message.embeds[0].remove_field(0)

            emb = game_win(self.enemies[self.curr], log, self.stats, self.author, self.drop)

            await self.stop()

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Востановление", style=discord.ButtonStyle.grey, emoji="💚", row=1)
    async def hp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False

    @discord.ui.button(label="Убежать", style=discord.ButtonStyle.grey, emoji="🚪", row=1)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False

    async def on_timeout(self) -> None:
        if self.game_end:
            return

        self.attack.disabled = True
        self.run.disabled = True
        self.hp.disabled = True
        self.select.disabled = False

        loss_cash = int(self.bot.users_db.find_one({"_id": self.author.id})['cash'] / 100 * 20)
        loss_exp = int(self.bot.users_db.find_one({"_id": self.author.id})['exp'] / 100 * 20)

        self.bot.users_db.update_one({"_id": self.author.id}, {"$inc": {"cash": -loss_cash, "exp": -loss_exp}})

        if self.interaction is None:
            return

        if len(self.interaction.message.embeds[0].fields) != 0:
            for i in range(len(self.interaction.message.embeds[0].fields)):
                self.interaction.message.embeds[0].remove_field(0)

        log = f"Пока вы бездействовали противник напал и убил вас. Вы потеряли {loss_cash} монет и {loss_exp} опыта\n"

        emb = discord.Embed(title=f"Время вышло, вы проиграли", description="\u200b")
        emb.add_field(name="Логи", value=log, inline=False)
        emb.set_thumbnail(url=self.enemies[self.curr]['url'])

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


class Select_dungeon(discord.ui.View):
    def __init__(self):
        super().__init__()


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super(Dungeon, self).__init__()

    @app_commands.command(name="dungeon")
    async def dungeon(self, interaction: discord.Interaction):
        mob = {
            "name": "uwu",
            "lvl": 1,
            'heal': 20,
            'damage': 1,
            'defence': None,
            'max_def': None,
            'max_hp': 40,
            'speed': 0,
            'luck': 0,
            'krit': 0,
            "url": "https://bots.server-discord.com/img/testback.png"
        }
        mob2 = {
            "name": "ywy",
            "lvl": 1,
            'heal': 30,
            'damage': 1,
            'defence': None,
            'max_def': None,
            'max_hp': 40,
            'speed': 0,
            'luck': 0,
            'krit': 0,
            "url": "https://bots.server-discord.com/img/testback.png"
        }
        mob3 = {
            "name": "owo",
            "lvl": 1,
            'heal': 40,
            'damage': 1,
            'defence': None,
            'max_def': None,
            'max_hp': 40,
            'speed': 0,
            'luck': 0,
            'krit': 0,
            "url": "https://bots.server-discord.com/img/testback.png"
        }

        enemy = [mob, mob2, mob3]
        us_stats = stats_calc(self.bot, interaction.user)
        view = Dun(self.bot, interaction.user, interaction, enemy, us_stats)
        await interaction.response.send_message(embed=game_emb(us_stats, enemy[0]), view=view)


async def setup(client):
    pass
    # await client.add_cog(Dungeon(client))
