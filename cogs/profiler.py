import random

import discord
from discord import app_commands
from discord.ext import commands

from modules import checker


def lvl_up(bot, user):
    us = bot.users_db.find_one({"_id": user.id})
    if us['exp_to_lvl'] <= us['exp']:
        bot.users_db.update_one({"_id": user.id}, {"$set": {"exp": 0},
                                                   "$inc": {"exp_to_lvl": us['exp_to_lvl'] / 5, "lvl": 1,
                                                            "skill_points": 3}})
        return True

    return False


def stats_get(stats):
    names = {
        "hp": "Хп",
        "damage": "Урон",
        "defence": "Защита",
        "speed": "Скорость",
        "krit": "Крит",
        "luck": "Удача"
    }
    sts = ""
    for i in stats:
        sts += names[i] + ": " + str(stats[i]) + "|"
    return sts


class Up_Skills(discord.ui.View):
    def __init__(self, author, bot):
        super().__init__()
        self.author = author
        self.stats = None
        self.interaction = None
        self.bot = bot

        self.upd()

    def upd(self):

        self.stats = self.bot.users_db.find_one({"_id": self.author.id})

        self.heal.label = f"{self.stats['hp']} - хп"
        self.armor.label = f"{self.stats['defence']} - броня"
        self.dmg.label = f"{self.stats['damage']} - урон"
        self.speed.label = f"{self.stats['speed']} - ловкость"
        self.luck.label = f"{self.stats['luck']} - удача"
        self.krit.label = f"{self.stats['krit']} - крит"

        self.upd2()

    def upd2(self):
        if self.stats['skill_points'] <= 0:
            self.armor.disabled = True
            self.dmg.disabled = True
            self.speed.disabled = True
            self.luck.disabled = True
            self.krit.disabled = True

        self.upd3()

    def upd3(self):
        if self.stats['lvl'] <= self.stats['defence']:
            self.armor.disabled = True
        if self.stats['lvl'] <= self.stats['damage']:
            self.dmg.disabled = True
        if self.stats['lvl'] <= self.stats['speed']:
            self.speed.disabled = True
        if self.stats['lvl'] <= self.stats['luck']:
            self.luck.disabled = True
        if self.stats['lvl'] <= self.stats['krit']:
            self.krit.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.interaction = interaction
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=checker.err_embed(f"Вам нельзя взаимодействовать с этим"),
                                                    ephemeral=True)

        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        if self.interaction is None:
            return

        self.armor.disabled = True
        self.dmg.disabled = True
        self.speed.disabled = True
        self.luck.disabled = True
        self.krit.disabled = True
        self.profile.disabled = True

        await self.interaction.message.edit(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=0, emoji='<:health:997889169567260714> ',
                       disabled=True)
    async def heal(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=0, emoji='<:armor:997889166673186987> ')
    async def armor(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats = self.bot.users_db.find_one({"_id": self.author.id})
        if self.stats['skill_points'] > 0:
            self.bot.users_db.update_many({"_id": self.author.id}, {"$inc": {"defence": 1, "skill_points": -1}})
        self.upd()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=1, emoji='<:strength:997889205684420718>')
    async def dmg(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats = self.bot.users_db.find_one({"_id": self.author.id})
        if self.stats['skill_points'] > 0:
            self.bot.users_db.update_many({"_id": self.author.id}, {"$inc": {"damage": 1, "skill_points": -1}})
        self.upd()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=1, emoji='<:luck:997889165221957642>')
    async def luck(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats = self.bot.users_db.find_one({"_id": self.author.id})
        if self.stats['skill_points'] > 0:
            self.bot.users_db.update_many({"_id": self.author.id}, {"$inc": {"luck": 1, "skill_points": -1}})
        self.upd()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=2, emoji='<:dexterity:997889168216694854>')
    async def speed(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats = self.bot.users_db.find_one({"_id": self.author.id})
        if self.stats['skill_points'] > 0:
            self.bot.users_db.update_many({"_id": self.author.id}, {"$inc": {"speed": 1, "skill_points": -1}})
        self.upd()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, row=2, emoji='<:crit:997889163552628757>')
    async def krit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stats = self.bot.users_db.find_one({"_id": self.author.id})
        if self.stats['skill_points'] > 0:
            self.bot.users_db.update_many({"_id": self.author.id}, {"$inc": {"krit": 1, "skill_points": -1}})
        self.upd()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Профиль", style=discord.ButtonStyle.blurple, row=3,
                       emoji='<:profile:1004832756364234762>')
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        us = self.bot.users_db.find_one({"_id": interaction.user.id})

        stats = {'hp': str(us['hp']),
                 'damage': str(us['damage']),
                 'defence': str(us['defence']),
                 'speed': str(us['speed']),
                 'luck': str(us['luck']),
                 'krit': str(us['krit']),
                 'skill_points': str(us['skill_points'])}

        plus_stats = {'hp': 0,
                      'damage': 0,
                      'defence': 0,
                      'speed': 0,
                      'luck': 0,
                      'krit': 0}

        for i in us['equipment'].keys():
            sel = us['equipment'][i]
            if sel is None:
                continue

            item = self.bot.items_db.find_one({"_id": sel})
            for f in item['give_stats'].keys():
                plus_stats[f] += item['give_stats'][f]

        for i in plus_stats.keys():
            if plus_stats[i] > 0:
                stats[i] += "+" + str(plus_stats[i])

        emb = discord.Embed(title=f"Профиль {interaction.user.name}", description="")
        emb.add_field(name="Уровень", value=us['lvl'], inline=False)
        emb.add_field(name="Опыт", value=str(round(us['exp'])) + '\\' + str(round(us['exp_to_lvl'])), inline=True)
        emb.add_field(name="Балланс", value=f"<:silver:997889161484828826> : {us['cash']}", inline=True)
        emb.add_field(name="Очки навыков", value=f"{stats['skill_points']}", inline=True)
        emb.add_field(name="Статы", value=f"<:health:997889169567260714> : {stats['heal']} | "
                                          f"<:strength:997889205684420718> : {stats['damage']} | "
                                          f"<:armor:997889166673186987> : {stats['defence']} \n"
                                          f"<:dexterity:997889168216694854> : {stats['speed']} | "
                                          f"<:luck:997889165221957642> : {stats['luck']} | "
                                          f"<:crit:997889163552628757> : {stats['krit']}",
                      inline=False)

        await interaction.response.edit_message(embed=emb, view=Inventory(interaction.user, interaction.user, self.bot))

    async def on_error(self, interaction, error: Exception, item):
        if isinstance(error, TimeoutError):
            await self.on_timeout()

        else:
            await interaction.response.edit_message()


class Inventory(discord.ui.View):
    def __init__(self, member, author, bot):
        super().__init__()
        self.author = author
        self.member = member
        self.interaction = None
        self.bot = bot
        if self.author.id != self.member.id:
            self.lvl.disabled = True

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=checker.err_embed(
                f"Вам нельзя взаимодействовать с этим"), ephemeral=True)
            return False

        return True

    @discord.ui.button(label="Профиль", style=discord.ButtonStyle.blurple, row=0,
                       emoji='<:profile:1004832756364234762>', disabled=True)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interaction = interaction
        self.left.disabled = True
        self.right.disabled = False
        self.central.disabled = False

        us = self.bot.users_db.find_one({"_id": self.member.id})

        stats = {'hp': str(us['hp']),
                 'damage': str(us['damage']),
                 'defence': str(us['defence']),
                 'speed': str(us['speed']),
                 'luck': str(us['luck']),
                 'krit': str(us['krit']),
                 'skill_points': str(us['skill_points'])}

        plus_stats = {'hp': 0,
                      'damage': 0,
                      'defence': 0,
                      'speed': 0,
                      'luck': 0,
                      'krit': 0}

        for i in us['equipment'].keys():
            sel = us['equipment'][i]
            if sel is None:
                continue

            item = self.bot.items_db.find_one({"_id": sel})
            for f in item['give_stats'].keys():
                plus_stats[f] += item['give_stats'][f]

        for i in plus_stats.keys():
            if plus_stats[i] > 0:
                stats[i] += "+" + str(plus_stats[i])

        emb = discord.Embed(title=f"Профиль {self.member.name}", description="")
        emb.add_field(name="Уровень", value=us['lvl'], inline=False)
        emb.add_field(name="Опыт", value=str(round(us['exp'])) + '\\' + str(round(us['exp_to_lvl'])), inline=True)
        emb.add_field(name="Балланс", value=f"<:silver:997889161484828826> : {us['cash']}", inline=True)
        emb.add_field(name="Очки навыков", value=f"{stats['skill_points']}", inline=True)
        emb.add_field(name="Статы", value=f"<:health:997889169567260714> : {stats['heal']} | "
                                          f"<:strength:997889205684420718> : {stats['damage']} | "
                                          f"<:armor:997889166673186987> : {stats['defence']} \n"
                                          f"<:dexterity:997889168216694854> : {stats['speed']} | "
                                          f"<:luck:997889165221957642> : {stats['luck']} | "
                                          f"<:crit:997889163552628757> : {stats['krit']}",
                      inline=False)

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Экипировка", style=discord.ButtonStyle.blurple, row=0,
                       emoji='<:equipment:1004832754661343232>')
    async def central(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interaction = interaction
        self.central.disabled = True
        self.left.disabled = False
        self.right.disabled = False

        us = self.bot.users_db.find_one({"_id": self.member.id})

        emb = discord.Embed(title=f"Экипировка {self.member.name}", description="")

        if us['equipment']['helmet'] is None:
            emb.add_field(name="Шлем", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['helmet']})
            emb.add_field(name=f"Шлем - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        if us['equipment']['armor'] is None:
            emb.add_field(name="Нагрудник", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['armor']})
            emb.add_field(name=f"Нагрудник - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        if us['equipment']['pants'] is None:
            emb.add_field(name="Штаны", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['pants']})
            emb.add_field(name=f"Штаны - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        if us['equipment']['shoes'] is None:
            emb.add_field(name="Ботинки", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['shoes']})
            emb.add_field(name=f"Ботинки - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        if us['equipment']['gloves'] is None:
            emb.add_field(name="Перчатки", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['gloves']})
            emb.add_field(name=f"Перчатки - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        if us['equipment']['weapon'] is None:
            emb.add_field(name="Оружие", value="Не надето", inline=True)
        else:
            item = self.bot.items_db.find_one({"_id": us['equipment']['weapon']})
            emb.add_field(name=f"Оружие - {item['name']}", value=stats_get(item['give_stats']), inline=True)

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Инвентарь", style=discord.ButtonStyle.blurple, row=0,
                       emoji='<:inventory:1004832752878768128>')
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interaction = interaction
        await checker.check(self.bot, interaction)
        self.central.disabled = False
        self.left.disabled = False
        self.right.disabled = True
        us = self.bot.users_db.find_one({"_id": self.member.id})
        emb = discord.Embed(title=f'Инвентарь {self.member.name}')

        items = {}
        for i in us['inventory']:
            if i is None:
                continue

            if i in items:
                items[i] += 1
            else:
                items[i] = 1

        counter = 1

        for i in items.keys():
            item = self.bot.items_db.find_one({"_id": i})
            emb.add_field(name=f"id: {counter}|{item['lvl']}lvl - {item['name']} x {items[i]}шт",
                          value=item['description'],
                          inline=False)
            counter += 1

        emb.set_footer(text=f"{us['inventory'].__len__()}/30")

        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Прокачать навыки", style=discord.ButtonStyle.blurple, row=1,
                       emoji='<:lvl_up:1006270950989365318>')
    async def lvl(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="Прокачка навыков", description="Выберите навык")
        await interaction.response.edit_message(embed=emb, view=Up_Skills(interaction.user, self.bot))

    async def on_timeout(self) -> None:
        self.left.disabled = True
        self.right.disabled = True
        self.central.disabled = True
        self.lvl.disabled = True

        if self.interaction is not None:
            await self.interaction.message.edit(view=self)

        await self.stop()

    async def stop(self) -> None:
        return


class Profiler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="посмотреть профиль")
    @app_commands.describe(member="пользователь профиль которого вы хотите посмотреть")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        await checker.check(self.bot, interaction)
        if member is None:
            member = interaction.user

        us = self.bot.users_db.find_one({"_id": member.id}) or None
        if us is None:
            await interaction.response.send_message(embed=checker.err_embed(
                f"Пользователь {member.name} ещё не пользовался ботом, у его нет "
                f"профиля"), ephemeral=True)
            return

        stats = {'hp': str(us['hp']),
                 'damage': str(us['damage']),
                 'defence': str(us['defence']),
                 'speed': str(us['speed']),
                 'luck': str(us['luck']),
                 'krit': str(us['krit']),
                 'skill_points': str(us['skill_points'])}

        plus_stats = {'hp': 0,
                      'damage': 0,
                      'defence': 0,
                      'speed': 0,
                      'luck': 0,
                      'krit': 0}

        for i in us['equipment'].keys():
            sel = us['equipment'][i]
            if sel is None:
                continue

            item = self.bot.items_db.find_one({"_id": sel})
            for f in item['give_stats'].keys():
                plus_stats[f] += item['give_stats'][f]

        for i in plus_stats.keys():
            if plus_stats[i] > 0:
                stats[i] += "+" + str(plus_stats[i])

        emb = discord.Embed(title=f"Профиль {member.name}", description="")
        emb.add_field(name="Уровень", value=us['lvl'], inline=False)
        emb.add_field(name="Опыт", value=str(round(us['exp'])) + '\\' + str(round(us['exp_to_lvl'])), inline=True)
        emb.add_field(name="Балланс", value=f"<:silver:997889161484828826> : {us['cash']}", inline=True)
        emb.add_field(name="Очки навыков", value=f"{stats['skill_points']}", inline=True)
        emb.add_field(name="Статы", value=f"<:health:997889169567260714> : {stats['heal']} | "
                                          f"<:strength:997889205684420718> : {stats['damage']} | "
                                          f"<:armor:997889166673186987> : {stats['defence']} \n"
                                          f"<:dexterity:997889168216694854> : {stats['speed']} | "
                                          f"<:luck:997889165221957642> : {stats['luck']} | "
                                          f"<:crit:997889163552628757> : {stats['krit']}",
                      inline=False)

        await interaction.response.send_message(embed=emb, view=Inventory(member, interaction.user, self.bot))

    @app_commands.command(name="equip", description="одеть вещь")
    @app_commands.describe(id="id предмета в вашем инвентаре")
    async def equip(self, interaction: discord.Interaction, id: int):
        await checker.check(self.bot, interaction)
        us = self.bot.users_db.find_one({"_id": interaction.user.id})
        items = {}
        for i in us['inventory']:
            if i in items:
                items[i] += 1
            else:
                items[i] = 1

        if id > items.__len__() or id < 1:
            await interaction.response.send_message(embed=checker.err_embed(
                f"У вас нет предмета с указанным id"), ephemeral=True)
            return

        counter = 1
        for i in items.keys():
            if counter == id:
                item = self.bot.items_db.find_one({"_id": i})
                if item['type'] == 'scroll' or item['type'] == 'potion' or item['type'] == 'extra':
                    await interaction.response.send_message(
                        embed=checker.err_embed(f"Вы не можете экипировать эту вещь")
                        , ephemeral=True)
                    return
                else:
                    if us['equipment'][item['type']] is None:
                        self.bot.users_db.update_one({"_id": interaction.user.id},
                                                     {"$set": {"equipment." + item['type']: i}})
                        item = self.bot.items_db.find_one({"_id": i})
                        us['inventory'].remove(i)
                        self.bot.users_db.update_one({"_id": interaction.user.id},
                                                     {"$set": {"inventory": us['inventory']}})
                        await interaction.response.send_message(embed=checker.emp_embed(f"Вы одели {item['name']}"))
                        return
                    else:
                        unek = self.bot.users_db.find_one({"_id": interaction.user.id})['equipment'][item['type']]
                        info = self.bot.items_db.find_one({"_id": unek})

                        self.bot.users_db.update_one({"_id": interaction.user.id},
                                                     {"$set": {"equipment." + item['type']: i}})
                        us['inventory'].remove(i).append(unek)

                        self.bot.users_db.update_one({"_id": interaction.user.id},
                                                     {"$set": {"inventory": us['inventory']}})
                        await interaction.response.send_message(embed=checker.emp_embed(f"Вы сняли {info['name']} "
                                                                                        f"и одели {item['name']}"))

                    return

            counter += 1

    @app_commands.command(name="unequip", description="Снять вещь")
    @app_commands.choices(type=[app_commands.Choice(name="Шлем", value="helmet"),
                                app_commands.Choice(name="Нагрудник", value="armor"),
                                app_commands.Choice(name="Штаны", value="pants"),
                                app_commands.Choice(name="Ботинки", value="shoes"),
                                app_commands.Choice(name="Перчатки", value="gloves"),
                                app_commands.Choice(name="Оружие", value="weapon")])
    @app_commands.describe(type="слот вещи, которую вы хотите снять")
    async def unequip(self, interaction: discord.Interaction, type: str):
        await checker.check(self.bot, interaction)
        us = self.bot.users_db.find_one({"_id": interaction.user.id})
        if us['equipment'][type] is None:
            await interaction.response.send_message(embed=checker.err_embed(f"В этом слоте ничего нет"),
                                                    ephemeral=True)
            return
        item = self.bot.items_db.find_one({"_id": us['equipment'][type]})
        self.bot.users_db.update_one({"_id": interaction.user.id}, {"$set": {"equipment." + type: None}})
        us['inventory'].append(item['_id'])
        self.bot.users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": us['inventory']}})
        await interaction.response.send_message(embed=checker.emp_embed(
            f"Вы сняли `{item['name']}` и положили в инвентарь"))

    @app_commands.command(name="sell", description="Продать вещь за 20% от цены")
    @app_commands.describe(id="id предмета в вашем инвентаре")
    async def sell(self, interaction: discord.Interaction, id: int):
        await checker.check(self.bot, interaction)
        us = self.bot.users_db.find_one({"_id": interaction.user.id})
        items = {}
        for i in us['inventory']:
            if i in items:
                items[i] += 1
            else:
                items[i] = 1

        if id > items.__len__() or id < 1:
            await interaction.response.send_message(embed=checker.err_embed(f"У вас нет предмета с указанным id"),
                                                    ephemeral=True)
            return

        counter = 1
        for i in items.keys():
            if counter == id:
                item = self.bot.items_db.find_one({"_id": i})
                us['inventory'].remove(i)

                self.bot.users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": us['inventory']}})
                self.bot.users_db.update_one({"_id": interaction.user.id}, {"$inc": {"cash": int(item['price'] * 0.2)}})
                await interaction.response.send_message(embed=checker.emp_embed(
                    f"Вы продали {item['name']} за {int(item['price'] * 0.2)}"))

            counter += 1

    @app_commands.command(name="work", description="Отправится в городской патруль")
    @app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        await checker.check(self.bot, interaction)
        us = self.bot.users_db.find_one({"_id": interaction.user.id})

        exp = 10 + random.randint(0, 2 * us['luck'])
        cash = 10 + random.randint(0, 2 * us['luck'])

        self.bot.users_db.update_many({"_id": interaction.user.id},
                                      {"$inc": {"exp": exp, "cash": cash}})

        rand = random.randint(1, 3)

        if rand == 1:

            emb = discord.Embed(title=f'**Городской патруль:**',
                                description=f'*Вы помогли городской стражи, отстояв за них на посту некоторое время.\n'
                                            f'Награда: {exp} exp и {cash} монет*')
            emb.set_thumbnail(url="https://cdn.discordapp.com/attachments/939111963559088200/1006659882470080552/"
                                  "Neznakomec_night_medieval_city_patrol_with_two_other_guards_fro_ff05944e-dd3d-4e2e"
                                  "-bd5e-52d3e9d3ffdc.png")
        elif rand == 2:
            emb = discord.Embed(title=f'**Харчевник:**',
                                description=f'*Вы помогли работником харчервина.\n'
                                            f'Награда: {exp} exp и {cash} монет*')
            emb.set_thumbnail(url="https://cdn.discordapp.com/attachments/939111963559088200/1006657127630245949"
                                  "/Neznakomec_view_of_the_bar_in_a_medieval_bar_815c4046-e52d-4f73-9328-"
                                  "b1e04386c28d.png")

        else:
            emb = discord.Embed(title=f'**Морской порт:**',
                                description=f'*Вы помогли разгрузить несколько грузовых кораблей.\n'
                                            f'Награда: {exp} exp и {cash} монет*')
            emb.set_thumbnail(url="https://cdn.discordapp.com/attachments/939111963559088200/1006967677434216580"
                                  "/Neznakomec_industrial_area_of_a_medieval_seaport_where_people_u_877e94cf"
                                  "-5f6f-4961-b79e-18d8c5e2ff00.png")

        lvl_up(self.bot, interaction.user)

        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="item_info", description="Посмотреть информацию о предмете")
    @app_commands.describe(id="id предмета в вашем инвентаре, либо глобальный uid предмета, либо название предмета")
    async def item_info(self, interaction: discord.Interaction, id: str):
        if id.__len__() > 2:
            item = self.bot.items_db.find_one({"_id": id}) or None

            if item is None:
                item = self.bot.items_db.find_one({"name": id}) or None

            if item is None:
                await interaction.response.send_message(embed=checker.err_embed(f"Предмет с таким uid, либо названием"
                                                                                f" не найден"),
                                                        ephemeral=True)
                return

        else:
            try:
                id = int(id)
            except ValueError:
                await interaction.response.send_message(embed=checker.err_embed(f"id указан неверно"),
                                                        ephemeral=True)
                return

            us = self.bot.users_db.find_one({"_id": interaction.user.id})
            await checker.check(self.bot, interaction)

            items = {}
            for i in us['inventory']:
                if i in items:
                    items[i] += 1
                else:
                    items[i] = 1

            if id > items.__len__() or id < 1:
                await interaction.response.send_message(embed=checker.err_embed(f"У вас нет предмета с указанным id"),
                                                        ephemeral=True)
                return

            item = None

            counter = 1
            for i in items.keys():
                if counter == id:
                    item = self.bot.items_db.find_one({"_id": i})

        color = {
            "common": 0xffffff,
            "uncommon": 0x0033cc,
            "rare": 0x6600ff,
            "epic": 0xffcc00,
            "legendary": 0xcc0000,
            "impossible": 0x000000,
            "exotic": 0xcc0066,
            "prize": 0xcccc00,
            "event": 0x666600
        }

        emb = discord.Embed(title=f'**Информация о {item["name"]}**', color=color[item["rarity"]])
        emb.add_field(name="Тип", value=item['type'])
        emb.add_field(name="Уровень", value=item['lvl'])
        emb.add_field(name="Редкость", value=item['rarity'])
        emb.add_field(name="Описание", value=item['description'])
        stats = stats_get(item['give_stats'])
        if stats == "":
            stats = "-"
        emb.add_field(name="Статы", value=stats)
        emb.add_field(name="uid", value=item['_id'])
        if 'image' in item:
            emb.set_thumbnail(url=item['image'])

        await interaction.response.send_message(embed=emb)


async def setup(client):
    await client.add_cog(Profiler(client))
