import uuid

import discord
from discord import app_commands
from discord.ext import commands

from modules import checker


def check(author, channel):
    def inner_check(message):
        return message.author == author and message.channel == channel

    return inner_check


class Devel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx) -> bool:
        if ctx.author.id == self.bot.owner_id:
            return True
        else:
            await ctx.channel.send(
                embed=checker.err_embed("Это техническая комманда, у вас недостаточно прав для её использования"),
                delete_after=15)
            return False

    @app_commands.command(name="add_loc")
    async def add_loc(self, interaction: discord.Interaction, lvl: int, name: str, monsters: str, urls: str,
                      description: str):
        if len(monsters) != len(urls):
            await interaction.response.send_message("Количество монстров и картинок не совпадает")
            return

        monsters = monsters.split()
        urls = urls.split()

        url = {}
        for i in range(len(monsters)):
            url[monsters[i]] = urls[i]

        post = \
            {
                "lvl": lvl,
                "name": name,
                "monsters": monsters,
                "urls": url,
                "drop": [],
                "description": description,
            }

        self.bot.info_db.update_one({"_id": "locations"}, {"$push": {"locations": post}})

        await interaction.response.send_message("Локация добавлена")

    @app_commands.command(name="rem_loc")
    async def rem_loc(self, interaction: discord.Interaction, name: str):

        self.bot.info_db.update_one({"_id": "locations"}, {"$pull": {"locations": {"name": name}}})
        await interaction.response.send_message("Локация удалена")

    @app_commands.command(name="create_item")
    @app_commands.choices(type=[app_commands.Choice(name="helmet", value="helmet"),
                                app_commands.Choice(name="armor", value="armor"),
                                app_commands.Choice(name="pants", value="pants"),
                                app_commands.Choice(name="shoes", value="shoes"),
                                app_commands.Choice(name="gloves", value="gloves"),
                                app_commands.Choice(name="weapon", value="weapon"),
                                app_commands.Choice(name="scroll", value="scroll"),
                                app_commands.Choice(name="potion", value="potion"),
                                app_commands.Choice(name="extra", value="extra")],
                          rarity=[app_commands.Choice(name="common", value="common"),
                                  app_commands.Choice(name="uncommon", value="uncommon"),
                                  app_commands.Choice(name="rare", value="rare"),
                                  app_commands.Choice(name="epic", value="epic"),
                                  app_commands.Choice(name="legendary", value="legendary"),
                                  app_commands.Choice(name="impossible", value="impossible"),
                                  app_commands.Choice(name="event", value="event"),
                                  app_commands.Choice(name="prize", value="prize"),
                                  app_commands.Choice(name="exotic", value="exotic")])
    async def create_item(self, interaction: discord.Interaction, name: str, lvl: int, type: str, price: int,
                          description: str, rarity: str):

        uid = str(uuid.uuid4())

        post = \
            {
                "_id": uid,
                "name": name,
                "lvl": lvl,
                "type": type,
                "price": price,
                "description": description,
                "rarity": rarity,
                "give_stats": {},
            }

        self.bot.items_db.insert_one(post)

        await interaction.response.send_message(f"Предмет добавлен, id предмета `{uid}`")

    @app_commands.command(name="rem_item")
    async def rem_item(self, interaction: discord.Interaction, name: str):
        self.bot.items_db.delete_one({"name": name})
        await interaction.response.send_message("Предмет удален")

    @app_commands.command(name="add_stat")
    @app_commands.choices(stat=[app_commands.Choice(name="hp", value="hp"),
                                app_commands.Choice(name="damage", value="damage"),
                                app_commands.Choice(name="defence", value="defence"),
                                app_commands.Choice(name="speed", value="speed"),
                                app_commands.Choice(name="krit", value="krit"),
                                app_commands.Choice(name="luck", value="luck")])
    async def add_stat(self, interaction: discord.Interaction, id: str, stat: str, value: int):
        self.bot.items_db.update_one({"_id": id}, {"$set": {"give_stats." + stat: value}})
        await interaction.response.send_message("Стат изменен")

    @app_commands.command(name="add_to_shop")
    async def add_to_shop(self, interaction: discord.Interaction, item_id: str):
        item = self.bot.items_db.find_one({"_id": item_id}) or None
        if item is None:
            await interaction.response.send_message("Предмет не найден")
            return

        post = \
            {
                "_id": item["_id"],
                "type": item["type"],
                "name": item["name"],
                "lvl": item["lvl"],
                "price": item["price"],
                "description": item["description"]
            }

        self.bot.info_db.update_one({"_id": "shop"}, {"$push": {"items": post}})

        await interaction.response.send_message("Добавлено в магазин")

    @app_commands.command(name="rem_from_shop")
    async def rem_from_shop(self, interaction: discord.Interaction, item_id: str):
        self.bot.info_db.update_one({"_id": "shop"}, {"$pull": {"items": item_id}})
        await interaction.response.send_message("Удалено из магазина")

    @app_commands.command(name="give_item")
    async def give_item(self, interaction: discord.Interaction, us_id: str, item_id: str):
        try:
            us_id = int(us_id)
        except ValueError:
            await interaction.response.send_message("Неверный id пользователя")
            return

        if self.bot.users_db.count_documents({"_id": us_id}) == 0:
            await interaction.response.send_message("пользователя не существует")
            return
        if self.bot.items_db.count_documents({"_id": item_id}) == 0:
            await interaction.response.send_message("предмета не существует")
            return

        item = self.bot.items_db.find_one({"_id": item_id})

        self.bot.users_db.update_one({"_id": us_id}, {"$push": {"inventory": item['_id']}})
        await interaction.response.send_message(f"Предмет `{item['_id']}` добавлен в инвентарь {us_id}")

    @app_commands.command(name="take_item", description="отобрать предмет")
    async def take_item(self, interaction: discord.Interaction, us_id: str, item_id: str):
        try:
            user = self.bot.get_user(int(us_id)) or None
        except ValueError:
            await interaction.response.send_message("Неверный id пользователя")
            return

        if self.bot.users_db.count_documents({"_id": user.id}) == 0 or user is None:
            await interaction.response.send_message("пользователя не существует")
            return
        if self.bot.items_db.count_documents({"_id": item_id}) == 0:
            await interaction.response.send_message("предмета не существует")
            return

        item = self.bot.items_db.find_one({"_id": item_id})

        self.bot.users_db.update_one({"_id": interaction.user.id}, {"$pull": {"inventory": item}})
        await interaction.response.send_message(f"Предмет `{item['_id']}` удален из инвентаря {user.id}")

    @app_commands.command(name="add_drop")
    async def add_drop(self, interaction: discord.Interaction, dungeon: str, item_id: str, chance: int):
        dungeons = self.bot.info_db.find_one({"_id": 'locations'})['loks'] or None
        counter = 0
        for i in dungeons:
            if i['name'].lower() == dungeon.lower():
                dungeon = i
                break
            counter += 1

        if dungeon is str:
            await interaction.response.send_message("Данной локации не существует")
            return

        if self.bot.items_db.count_documents({"_id": item_id}) == 0:
            await interaction.response.send_message("предмета не существует")
            return

        post = {
            item_id: chance
        }

        self.bot.info_db.update_one({"_id": "locations"},
                                    {"$set": {"loks." + str(counter) + ".drop." + item_id: chance}})

        await interaction.response.send_message(f"{item_id} добвлен на локацию с шансом 1\{chance}")

    @app_commands.command(name="add_image")
    async def add_image(self, interaction: discord.Interaction, id: str, image: str):
        if self.bot.items_db.count_documents({"_id": id}) == 0:
            await interaction.response.send_message("предмета не существует")
            return

        self.bot.items_db.update_one({"_id": id}, {"$set": {"image": image}})

        await interaction.response.send_message(f"Изображение добавлено для {id}")

    @app_commands.command(name="upd")
    async def upd(self, interaction: discord.Interaction):
        # change key from heal to hp
        self.bot.users_db.update_many({}, {"$rename": {"heal": "hp"}})
        self.bot.users_db.update_many({}, {"$rename": {"equipment.helet": "helmet"}})
        self.bot.info_db.update_many({"type": "helet"}, {"$rename": {"helet": "helmet"}})
        self.bot.items_db.update_many({}, {"$set": {"generated": True}})

        # self.bot.items_db.update_many({}, {"$set": {"give_stats": {
        #     "hp": 0,
        #     "damage": 0,
        #     "defence": 0,
        #     "luck": 0,
        #     "speed": 0
        # }}})
        # # remove key from items
        # self.bot.items_db.update_many({}, {"$unset": {"hp": "", "damage": "", "defence": "", "luck": "", "speed": ""}})
        await interaction.response.send_message("Обновлено")


async def setup(client):
    await client.add_cog(Devel(client))
    # pass
