import enum
import random

import discord
from discord import app_commands
from discord.ext import commands
import json

from modules import checker

works = None


class Interaction_type(enum.Enum):
    info = 1
    eqip = 2
    sell = 3


rarities = {'common': "обычный",
            'uncommon': "необыйчный",
            'rare': "редкий",
            'epic': "эпический",
            'legendary': "легендарый"}

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


def inventory_to_dict(arr: list[str]) -> dict:
    items = {}
    for i in arr:
        if i is None:
            continue

        if i in items:
            items[i] += 1
        else:
            items[i] = 1

    return items


def crete_page(bot, inv_dict: dict, inventory: list, start: int) -> list[discord.Embed, list[dict]]:
    items = inventory[start:start + 5]
    curr_page_items = []
    for i in items:
        curr_page_items.append(bot.items_db.find_one({"_id": i}))

    emb = discord.Embed(title="Инвентарь")
    for i in curr_page_items:
        desc = i['description'] or None
        if desc is None:
            desc = rarities[i['rarity']] + " | " + i['preset']
        emb.add_field(name=f"{curr_page_items.index(i) + 1}.  {i['lvl']} lvl - {i['name']} x {inv_dict[i['_id']]}шт",
                      value=desc,
                      inline=False)

    return [emb, curr_page_items]


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


def create_profile_emb(bot, member: discord.Member) -> discord.Embed:
    us = bot.users_db.find_one({"_id": member.id}) or None
    if us is None:
        return checker.err_embed(
            f"Пользователь {member.name} ещё не пользовался ботом, у его нет профиля")

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

        item = bot.items_db.find_one({"_id": sel})
        for f in item['give_stats'].keys():
            plus_stats[f] += item['give_stats'][f]

    for i in plus_stats.keys():
        if plus_stats[i] > 0:
            stats[i] += "+" + str(plus_stats[i])

    emb = discord.Embed(title=f"Профиль {member.name}", description="")
    emb.add_field(name="Уровень", value=us['lvl'], inline=False)
    emb.add_field(name="Опыт", value=str(round(us['exp'])) + '\\' + str(round(us['exp_to_lvl'])), inline=True)
    emb.add_field(name="Баланс", value=f"<:silver:997889161484828826> : {us['cash']}", inline=True)
    emb.add_field(name="Очки навыков", value=f"{stats['skill_points']}", inline=True)
    emb.add_field(name="Статы", value=f"<:health:997889169567260714> : {stats['hp']} | "
                                      f"<:strength:997889205684420718> : {stats['damage']} | "
                                      f"<:armor:997889166673186987> : {stats['defence']} \n"
                                      f"<:dexterity:997889168216694854> : {stats['speed']} | "
                                      f"<:luck:997889165221957642> : {stats['luck']} | "
                                      f"<:crit:997889163552628757> : {stats['krit']}",
                  inline=False)

    return emb


async def sell(bot, member, id, amount, interaction):
    us = bot.users_db.find_one({"_id": member.id})
    item = bot.items_db.find_one({"_id": id})
    count = 0
    while id in us['inventory'] and count < amount:
        us['inventory'].remove(id)
        count += 1

    bot.users_db.update_one({"_id": member.id}, {"$set": {"inventory": us['inventory']}})
    bot.users_db.update_one({"_id": member.id},
                            {"$inc": {"cash": int(item['price'] * 0.2 * count)}})

    await interaction.response.edit_message(embed=checker.emp_embed(
        f"Вы продали {item['name']} в количестве{count}шт. за {int(item['price'] * 0.2 * count)}"), view=None)


def lvl_up(bot, user):
    us = bot.users_db.find_one({"_id": user.id})
    if us['exp_to_lvl'] <= us['exp']:
        bot.users_db.update_one({"_id": user.id}, {"$set": {"exp": 0},
                                                   "$inc": {"exp_to_lvl": us['exp_to_lvl'] / 5, "lvl": 1,
                                                            "skill_points": 3}})
        return True

    return False


class Inventory(discord.ui.View):
    def __init__(self, bot, member, author, interaction, inventory, curr_page_items_list):
        super().__init__()
        self.author = author
        self.member = member
        self.interaction = interaction
        self.bot = bot

        self.inventory = inventory
        self.keys = list(self.inventory.keys())
        self.page_list = curr_page_items_list

        self.num_curr_page = 0

        self.buttons = [self.first, self.second, self.third, self.fourth, self.fifth]

        if self.keys.__len__() <= 5:
            self.right.disabled = True

        self.inter_type = Interaction_type.info

        self.update_buttons()

    def update_buttons(self):
        for i in self.buttons:
            i.disabled = True

        if not self.page_list:
            return

        types_to_eqip = ['helem', 'helmet', 'armor', 'pants', 'shoes', 'gloves', 'weapon']

        for i in range(self.page_list.__len__()):
            if self.inter_type == Interaction_type.eqip:
                if self.author.id == self.member.id and self.page_list[i]['type'] in types_to_eqip:
                    self.buttons[i].disabled = False

                continue
            else:
                self.buttons[i].disabled = False

    async def interact(self, num: int, interaction):

        inter_item = self.page_list[num-1]
        if self.inter_type == Interaction_type.info:
            emb = discord.Embed(title=f'**Информация о {inter_item["name"]}**', color=color[inter_item["rarity"]])
            emb.add_field(name="Тип", value=inter_item['type'])
            emb.add_field(name="Уровень", value=inter_item['lvl'])
            emb.add_field(name="Редкость", value=inter_item['rarity'])
            if 'generated' not in inter_item:
                emb.add_field(name="Описание", value=inter_item['description'])
            else:
                emb.add_field(name="Прессет", value=inter_item['preset'])
            stats = stats_get(inter_item['give_stats'])
            if stats == "":
                stats = "-"
            emb.add_field(name="Статы", value=stats)
            emb.add_field(name="uid", value=inter_item['_id'])

            if 'image' in inter_item:
                emb.set_thumbnail(url=inter_item['image'])

            await interaction.response.send_message(embed=emb)

        if self.inter_type == Interaction_type.eqip:
            user = self.bot.users_db.find_one({"_id": self.author.id})
            if user['equipment'][inter_item['type']] is None:
                self.bot.users_db.update_one({"_id": self.author.id},
                                             {"$set": {"equipment." + inter_item['type']: inter_item["_id"]}})
                user['inventory'].remove(inter_item["_id"])
                self.bot.users_db.update_one({"_id": self.author.id},
                                             {"$set": {"inventory": user['inventory']}})
                await interaction.response.send_message(f"Вы одели {inter_item['name']}")
                return
            else:
                unek = user['equipment'][inter_item['type']]
                info = self.bot.items_db.find_one({"_id": unek})

                self.bot.users_db.update_one({"_id": interaction.user.id},
                                             {"$set": {"equipment." + inter_item['type']: inter_item["_id"]}})
                user['inventory'].remove(inter_item["_id"])
                user['inventory'].append(unek)

                self.bot.users_db.update_one({"_id": interaction.user.id},
                                             {"$set": {"inventory": user['inventory']}})
                await interaction.response.send_message(f"Вы сняли {info['name']} "
                                                        f"и одели {inter_item['name']}")

        else:
            emb = discord.Embed(title=f"Продажа {inter_item['name']}",
                                description=f"Стоимость за 1 шт: {inter_item['price'] * 0.2}\n"
                                            f"В инвентаре: {self.inventory[inter_item['_id']]}\n"
                                            f"Выберете сколько хотите продать:")
            await interaction.response.send_message(embed=emb, view=To_Sell(self.bot, self.member, inter_item['_id']),
                                                    ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=checker.err_embed(
                f"Вам нельзя взаимодействовать с этим"), ephemeral=True)
            return False

        return True

    @discord.ui.select(placeholder="Вид Взаимодействие : информация", max_values=1, min_values=1, row=1,
                       options=
                       [discord.SelectOption(label="Больше информации"),
                        discord.SelectOption(label="Экипировать"),
                        discord.SelectOption(label="Продать")])
    async def select(self, interaction: discord.Interaction, options):
        if str(interaction.data["values"][0]) == "Больше информации":
            self.inter_type = Interaction_type.info
            self.select.placeholder = "Вид Взаимодействие : Больше информации"

            for i in self.buttons:
                i.style = discord.ButtonStyle.blurple

        if str(interaction.data["values"][0]) == "Экипировать":
            self.inter_type = Interaction_type.eqip
            self.select.placeholder = "Вид Взаимодействие : Экипировать"

            for i in self.buttons:
                i.style = discord.ButtonStyle.green

        if str(interaction.data["values"][0]) == "Продать":
            self.inter_type = Interaction_type.sell
            self.select.placeholder = "Вид Взаимодействие : Продать"

            for i in self.buttons:
                i.style = discord.ButtonStyle.red

        self.update_buttons()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple, row=0,
                       disabled=True)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.right.disabled = False
        self.num_curr_page -= 5
        text = ""
        if self.num_curr_page < 10:
            text += "0" + str(self.num_curr_page + 1)
        else:
            text += str(self.num_curr_page + 1)

        text += '-'

        if self.num_curr_page + 5 < 10:
            text += "0" + str(self.num_curr_page + 5)
        else:
            text += str(self.num_curr_page + 5)

        self.pages.label = text
        if self.num_curr_page <= 0:
            self.left.disabled = True

        page = crete_page(self.bot, self.inventory, list(self.inventory.keys()), self.num_curr_page)
        self.page_list = page[1]
        self.update_buttons()
        await interaction.response.edit_message(embed=page[0], view=self)
        pass

    @discord.ui.button(label="01-05", style=discord.ButtonStyle.grey, row=0,
                       disabled=True)
    async def pages(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple, row=0,
                       disabled=False)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.left.disabled = False
        self.num_curr_page += 5
        text = ""
        if self.num_curr_page < 10:
            text += "0" + str(self.num_curr_page + 1)
        else:
            text += str(self.num_curr_page + 1)

        text += '-'

        if self.num_curr_page + 5 < 10:
            text += "0" + str(self.num_curr_page + 5)
        else:
            text += str(self.num_curr_page + 5)

        self.pages.label = text
        if self.num_curr_page >= 25 or self.inventory.__len__() <= self.num_curr_page + 5:
            self.right.disabled = True

        page = crete_page(self.bot, self.inventory, list(self.inventory.keys()), self.num_curr_page)
        self.page_list = page[1]
        self.update_buttons()
        await interaction.response.edit_message(embed=page[0], view=self)
        pass

    @discord.ui.button(label="♻️", style=discord.ButtonStyle.grey, row=0)
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.inventory = inventory_to_dict(self.bot.users_db.find_one({"_id": self.member.id})["inventory"])
        self.keys = list(self.inventory.keys())
        page = crete_page(self.bot, self.inventory, self.keys, 0)
        self.page_list = page[1]

        if self.keys.__len__() <= 5:
            self.right.disabled = True
        else:
            self.right.disabled = False

        self.left.disabled = True

        self.pages.label = "01-05"
        self.num_curr_page = 0

        self.update_buttons()

        await interaction.response.edit_message(embed=page[0], view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.blurple, row=2,
                       disabled=False)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interact(1, interaction)
        pass

    @discord.ui.button(label="2", style=discord.ButtonStyle.blurple, row=2,
                       disabled=False)
    async def second(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interact(2, interaction)
        pass

    @discord.ui.button(label="3", style=discord.ButtonStyle.blurple, row=2,
                       disabled=False)
    async def third(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interact(3, interaction)
        pass

    @discord.ui.button(label="4", style=discord.ButtonStyle.blurple, row=2,
                       disabled=False)
    async def fourth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interact(4, interaction)
        pass

    @discord.ui.button(label="5", style=discord.ButtonStyle.blurple, row=2,
                       disabled=False)
    async def fifth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interact(5, interaction)
        pass

    @discord.ui.button(label="🔙 К профилю", style=discord.ButtonStyle.grey, row=3,
                       disabled=False)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=create_profile_emb(self.bot, self.member),
                                                view=Profile(self.member, self.author, self.bot))


class To_Sell(discord.ui.View):
    def __init__(self, bot, member: discord.Member, id: str):
        super().__init__()
        self.bot = bot
        self.id = id
        self.member = member
        self.inventory = self.bot.users_db.find_one({"_id": member.id})['inventory']
        self.counter = 0

        for i in self.inventory:
            if i == self.id:
                self.counter += 1

        if self.counter >= 1:
            self.first.disabled = False
            self.fifth.disabled = False

        if self.counter >= 2:
            self.second.disabled = False

        if self.counter >= 5:
            self.third.disabled = False

        if self.counter >= 10:
            self.fourth.disabled = False

    @discord.ui.button(label="1", style=discord.ButtonStyle.blurple, row=2,
                       disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        await sell(self.bot, self.member, self.id, 1, interaction)
        pass

    @discord.ui.button(label="2", style=discord.ButtonStyle.blurple, row=2,
                       disabled=True)
    async def second(self, interaction: discord.Interaction, button: discord.ui.Button):
        await sell(self.bot, self.member, self.id, 2, interaction)
        pass

    @discord.ui.button(label="5", style=discord.ButtonStyle.blurple, row=2,
                       disabled=True)
    async def third(self, interaction: discord.Interaction, button: discord.ui.Button):
        await sell(self.bot, self.member, self.id, 5, interaction)
        pass

    @discord.ui.button(label="10", style=discord.ButtonStyle.blurple, row=2,
                       disabled=True)
    async def fourth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await sell(self.bot, self.member, self.id, 10, interaction)
        pass

    @discord.ui.button(label="Всё", style=discord.ButtonStyle.blurple, row=2,
                       disabled=True)
    async def fifth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await sell(self.bot, self.member, self.id, 999, interaction)
        pass


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
        emb.add_field(name="Баланс", value=f"<:silver:997889161484828826> : {us['cash']}", inline=True)
        emb.add_field(name="Очки навыков", value=f"{stats['skill_points']}", inline=True)
        emb.add_field(name="Статы", value=f"<:health:997889169567260714> : {stats['hp']} | "
                                          f"<:strength:997889205684420718> : {stats['damage']} | "
                                          f"<:armor:997889166673186987> : {stats['defence']} \n"
                                          f"<:dexterity:997889168216694854> : {stats['speed']} | "
                                          f"<:luck:997889165221957642> : {stats['luck']} | "
                                          f"<:crit:997889163552628757> : {stats['krit']}",
                      inline=False)

        await interaction.response.edit_message(embed=emb, view=Profile(interaction.user, interaction.user, self.bot))

    async def on_error(self, interaction, error: Exception, item):
        if isinstance(error, TimeoutError):
            await self.on_timeout()

        else:
            await interaction.response.edit_message()


class Profile(discord.ui.View):
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

    @discord.ui.button(label="Профиль", style=discord.ButtonStyle.blurple, row=1,
                       emoji='<:profile:1004832756364234762>', disabled=True)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interaction = interaction
        self.left.disabled = True
        self.right.disabled = False
        self.central.disabled = False

        await interaction.response.edit_message(embed=create_profile_emb(self.bot, self.member), view=self)

    @discord.ui.button(label="Экипировка", style=discord.ButtonStyle.blurple, row=1,
                       emoji='<:equipment:1004832754661343232>')
    async def central(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interaction = interaction
        self.central.disabled = True
        self.left.disabled = False
        self.right.disabled = False

        us = self.bot.users_db.find_one({"_id": self.member.id})

        emb = discord.Embed(title=f"Экипировка {self.member.name}")

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

    @discord.ui.button(label="Инвентарь", style=discord.ButtonStyle.blurple, row=1,
                       emoji='<:inventory:1004832752878768128>')
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):

        invent = inventory_to_dict(self.bot.users_db.find_one({"_id": self.member.id})['inventory'])

        ada = crete_page(self.bot, invent, list(invent.keys()), 0)

        await interaction.response.edit_message(embed=ada[0],
                                                view=Inventory(self.bot, self.member, self.author, interaction, invent,
                                                               ada[1]))

    @discord.ui.button(label="Прокачать навыки", style=discord.ButtonStyle.blurple, row=2,
                       emoji='<:lvl_up:1006270950989365318>')
    async def lvl(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="Прокачка навыков",
                            description="Уровень навыка не может привышать уровень персонажа\n"
                                        "<:health:997889169567260714> - увеличивается только за счёт экипировки\n"
                                        "<:strength:997889205684420718> - наносимый урон\n"
                                        "<:armor:997889166673186987> - принимают на себя весь урон с его частичным уменьшением\n"
                                        "<:dexterity:997889168216694854> - увиличивает вероятность укланения\n"
                                        "<:luck:997889165221957642> - увеличивает получаемый опыт и монеты\n"
                                        "<:crit:997889163552628757> - вероятность критического удара")
        await interaction.response.edit_message(embed=emb, view=Up_Skills(interaction.user, self.bot))

    async def stop(self) -> None:
        return


class Profiler_com(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="посмотреть профиль")
    @app_commands.describe(member="пользователь профиль которого вы хотите посмотреть")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        emb = create_profile_emb(self.bot, member)
        if emb is None:
            return

        await interaction.response.send_message(embed=emb, view=Profile(member, interaction.user, self.bot))

    @app_commands.command(name="work", description="Отправится в городской патруль")
    # @app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        global works
        await checker.check(self.bot, interaction)
        us = self.bot.users_db.find_one({"_id": interaction.user.id})

        exp = 10 + random.randint(0, 2 * us['luck'])
        cash = 10 + random.randint(0, 2 * us['luck'])

        self.bot.users_db.update_many({"_id": interaction.user.id},
                                      {"$inc": {"exp": exp, "cash": cash}})

        if works is None:
            data = None
            with open('json\\works.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            works = data['works']

        rand = random.choice(works)

        emb = discord.Embed(title=rand['title'],
                            description=rand['description'].format(exp, cash))
        emb.set_thumbnail(url=rand['url'])

        lvl_up(self.bot, interaction.user)

        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="item_info", description="Посмотреть информацию о предмете")
    @app_commands.describe(id="глобальный uid предмета, либо название предмета")
    async def item_info(self, interaction: discord.Interaction, id: str):

        item = self.bot.items_db.find_one({"_id": id}) or None

        if item is None:
            item = self.bot.items_db.find_one({"name": id}) or None

        if item is None:
            await interaction.response.send_message(embed=checker.err_embed(f"Предмет с таким uid, либо названием"
                                                                            f" не найден"),
                                                    ephemeral=True)
            return

        emb = discord.Embed(title=f'**Информация о {item["name"]}**', color=color[item["rarity"]])
        emb.add_field(name="Тип", value=item['type'])
        emb.add_field(name="Уровень", value=item['lvl'])
        emb.add_field(name="Редкость", value=item['rarity'])
        if 'generated' not in item or not item['generated']:
            emb.add_field(name="Описание", value=item['description'])
        else:
            emb.add_field(name="Прессет", value=item['preset'])
        stats = stats_get(item['give_stats'])
        if stats == "":
            stats = "-"
        emb.add_field(name="Статы", value=stats)
        emb.add_field(name="uid", value=item['_id'])

        if 'image' in item:
            emb.set_thumbnail(url=item['image'])

        await interaction.response.send_message(embed=emb)


async def setup(client):
    await client.add_cog(Profiler_com(client))
