import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.profiler import lvl_up

from modules.classes import Player, Enemy

HEAL_POTION_ID = "fb75ff73-1116-4e95-ae46-8075c4e9a782"

'''
шо ещё надо делать (todo кароч):
1. рандомный дроп
3. удаление вещи из бд с вещами если ни у кого из пользователей данного предмета нет
'''


def game_emb(player: Player, enemy: Enemy, log):
    embed = discord.Embed(title=f"Битва с {enemy.name} - {enemy.lvl}", description="\u200b")
    embed.add_field(
        name=f"Вы - {player.lvl}",
        value=f"hp - {player.hp_bar()}\nброня - {player.defence_bar()}\nурон - {player.damage}"
    )

    embed.add_field(
        name=f"{enemy.name} - {enemy.lvl}",
        value=f"hp - {enemy.hp_bar()}\nброня - {enemy.defence_bar()}\nурон - {enemy.damage}",
        inline=False
    )

    if log is not None:
        embed.add_field(name="Лог", value=log, inline=False)

    embed.set_thumbnail(url=enemy.url)

    return embed


def game_loose(mob: Enemy, log, author, bot):
    loss_cash = int(bot.users_db.find_one({"_id": author.id})['cash'] / 5)
    loss_exp = int(bot.users_db.find_one({"_id": author.id})['exp'] / 5)

    bot.users_db.update_one({"_id": author.id}, {"$inc": {"cash": -loss_cash, "exp": -loss_exp}})

    log += f"Вы проиграли и потеряли {loss_cash} монет и {loss_exp} опыта\n"

    emb = discord.Embed(title=f"Проигрыш", description="\u200b")
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob.url)

    return emb


def game_win(mob: Enemy, log, player: Player, author, bot):
    exp = random.randint(mob.lvl * 3, mob.lvl * 5) + random.randint(0, 7 * player.luck)
    coins = mob.lvl * 3 + random.randint(0, 7 * player.luck)

    bot.users_db.update_many({"_id": author.id}, {"$inc": {"exp": exp, "cash": coins}})

    log += f"Вы победили\nВ качестве награды вы получили exp - {exp} и монет - {coins}\n"

    emb = discord.Embed(title=f"Победа", description="\u200b")
    if lvl_up(bot, author):
        log += f"Вы получили новый уровень\n"
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob.url)

    return emb


def game_run(mob: Enemy, log, author, bot):
    if random.randint(1, 5) == 1:
        cash = bot.users_db.find_one({"_id": author.id})['cash']
        cash -= int(cash / 100 * 5)
        bot.users_db.update_many({"_id": author.id}, {"$set": {"cash": cash}})
        log += f"В попыхах вы обранили {int(cash / 100 * 5)} монет\n"

    emb = discord.Embed(title=f"Побег", description="\u200b")
    emb.add_field(name="Логи", value=log, inline=False)
    emb.set_thumbnail(url=mob.url)

    return emb


class Dun(discord.ui.View):
    def __init__(self, bot, author, interaction: discord.Interaction, enemies: list[Enemy], player: Player):
        super().__init__()
        self.bot = bot

        self.player = player
        self.author = author
        self.interaction = interaction
        self.enemies = enemies
        self.curr = 0
        self.game_end = False
        self.drop = None
        self.inventory = self.bot.users_db.find_one({"_id": author.id})['inventory']
        self.upd_select()

    def upd_select(self):
        self.select.options = []
        self.select.add_option(label="1 - " + self.enemies[0].name,
                               description=f"{self.enemies[0].hp / self.enemies[0].max_hp * 100:.2f}%",
                               emoji="❤️",
                               value="0")

        self.select.add_option(label="2 - " + self.enemies[1].name,
                               description=f"{self.enemies[1].hp / self.enemies[1].max_hp * 100:.2f}%",
                               emoji="❤️",
                               value="1")

        self.select.add_option(label="3 - " + self.enemies[2].name,
                               description=f"{self.enemies[2].hp / self.enemies[2].max_hp * 100:.2f}%",
                               emoji="❤️",
                               value="2")

        for i in self.enemies:
            if i.hp == 0:
                self.select.options[self.enemies.index(i)].emoji = "☠️"
            if self.enemies.index(i) == self.curr:
                self.select.options[self.enemies.index(i)].emoji = "⚔️"

    @discord.ui.select(options=[], row=0, placeholder="Выберите противника")
    async def select(self, interaction: discord.Interaction, options):
        self.select.disabled = True
        self.curr = int(interaction.data["values"][0])
        self.upd_select()

        emb = game_emb(self.player, self.enemies[self.curr], None)
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Атаковать", style=discord.ButtonStyle.grey, emoji="⚔️", row=1)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False

        log = ""

        if random.randint(1, 100) < 1 + self.player.krit:
            damage = self.enemies[self.curr].get_damage(self.player.damage * 2)
            log += f"Вы нанесли критический удар, тем самым нанеся {damage:.2f} урона\n"
        else:
            damage = self.enemies[self.curr].get_damage(self.player.damage)
            log += f"Вы нанесли {damage:.2f} урона\n"

        dead = [False, False, False]
        for i in self.enemies:
            if i.hp <= 0:
                dead[self.enemies.index(i)] = True

        if not all(dead):
            for enemy in self.enemies:

                if enemy.hp > 0:

                    if random.randint(1, 100) != 1 + self.player.speed:
                        damage = self.player.get_damage(enemy.damage)
                        log += f"Монстр {self.enemies.index(enemy) + 1} - {enemy.name} нанес вам  {damage:.2f} урона\n"

                    else:
                        log += "Вы укланились от атаки\n"

                    if self.player.hp <= 0:
                        self.attack.disabled = True
                        self.run.disabled = True
                        self.hp.disabled = True

                        await self.stop()

                        await interaction.response.edit_message(
                            embed=game_loose(self.enemies[self.curr], log, self.author, self.bot),
                            view=self)

                        return

            emb = game_emb(self.player, self.enemies[self.curr], log)

        else:

            emb = game_win(self.enemies[self.curr], log, self.player, self.author, self.bot)

            await self.stop()

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Восстановление", style=discord.ButtonStyle.grey, emoji="💚", row=1)
    async def hp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False
        log = ""

        if self.player.rem_heal():
            log += f"Вы востановили {self.player.max_hp / 4} хп\n"

            if random.randint(1, 5) == 1:
                damage = self.player.get_damage(self.enemies[self.curr].damage)
                log += f"Притивнику удалось нанести вам {damage:.2f} урона\n"

                if self.player.hp <= 0:
                    await self.stop()

                    await interaction.response.edit_message(
                        embed=game_loose(self.enemies[self.curr], log, self.author, self.bot), view=self)

            else:
                log += "Притивнику не удалось ударить вас\n"

            self.interaction = await interaction.response.edit_message(
                embed=game_emb(self.player, self.enemies[self.curr], log),
                view=self)

            return

        log += "У вас нет зелья жизни\n"

        if random.randint(1, 5) == 1:
            damage = self.player.get_damage(self.enemies[self.curr].damage)
            log += f"Пока вы лазили по сумке, противник нанёс {damage:.2f} урона\n"

            if self.player.hp <= 0:
                await self.stop()
                await interaction.response.edit_message(
                    embed=game_loose(self.enemies[self.curr], log, self.author, self.bot),
                    view=self)

                return

        else:
            log += "Противнику не удалось ударить вас\n"

        emb = game_emb(self.player, self.enemies[self.curr], log)

        self.interaction = await interaction.response.edit_message(embed=emb, view=self)
        return

    @discord.ui.button(label="Убежать", style=discord.ButtonStyle.grey, emoji="🚪", row=1)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.select.disabled = False

        if 1 < random.randint(1, 100) < 25 + self.player.speed:
            self.attack.disabled = True
            self.run.disabled = True
            self.hp.disabled = True

            log = "Вам удалось спастись\n"
            await self.stop()

            self.interaction = await interaction.response.edit_message(
                embed=game_run(self.enemies[self.curr], log, self.author, self.bot),
                view=self)
            return
        if random.randint(1, 3) == 1:
            damage = self.player.get_damage(self.enemies[self.curr].damage)
            log = f"Пока вы пытались убежать противник ударил вас в спину, нанеся {damage:.2f} урона\n"

        else:
            log = f"Вам не удалось сбежать"

        if self.player.hp <= 0:
            await self.stop()
            await interaction.response.edit_message(
                embed=game_loose(self.enemies[self.curr], log, self.author, self.bot),
                view=self)

            return

        self.interaction = await interaction.response.edit_message(
            embed=game_emb(self.player, self.enemies[self.curr], log)
        )

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

        log = f"Пока вы бездействовали противник напал и убил вас. Вы потеряли {loss_cash} монет и {loss_exp} опыта\n"

        emb = discord.Embed(title=f"Время вышло, вы проиграли", description="\u200b")
        emb.add_field(name="Логи", value=log, inline=False)
        emb.set_thumbnail(url=self.enemies[self.curr].url)

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
        mob1 = Enemy("Тестовый моб 1", 2, "https://bots.server-discord.com/img/testback.png")
        mob2 = Enemy("Тестовый моб 2", 2, "https://bots.server-discord.com/img/testback.png")
        mob3 = Enemy("Тестовый моб 3", 2, "https://bots.server-discord.com/img/testback.png")

        player = Player(interaction.user, self.bot)

        enemy = [mob1, mob2, mob3]
        view = Dun(self.bot, interaction.user, interaction, enemy, player)
        await interaction.response.send_message(embed=game_emb(player, enemy[0], None), view=view)


async def setup(client):
    # pass
    await client.add_cog(Dungeon(client))
