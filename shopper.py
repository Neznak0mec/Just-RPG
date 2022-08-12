import discord
import pymongo
import discord
from discord import app_commands
from discord.ext import commands
import random
import checker
import os
from dotenv import load_dotenv

load_dotenv()

os.getenv()

connection = ""
cluster = pymongo.MongoClient(connection)
# todo: под замену
db = cluster["MMORPG"]

users_db = db["users"]
servers_db = db["servers"]
info_db = db["info"]
item_db = db["items"]


class Dropdown(discord.ui.Select):
    def __init__(self, bot):
        # Set the options that will be presented inside the dropdown
        self.bot = bot
        options = [
            discord.SelectOption(label='Свитки', description='Здесь вы можете купить свитки'),
            discord.SelectOption(label='Зелья', description='Здесь вы можете купитть зелья'),
            discord.SelectOption(label='Обмундирование', description='Здесь вы откроете меню обмундерования'),
        ]

        super().__init__(placeholder='Каталог товаров и услуг.', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if len(interaction.message.embeds[0].fields) != 0:
            for i in range(len(interaction.message.embeds[0].fields)):
                interaction.message.embeds[0].remove_field(0)

        slots = info_db.find_one({"_id": "shop"})['items']
        all = []

        if self.values[0] == 'Свитки':

            interaction.message.embeds[0].title = 'Свитки'
            interaction.message.embeds[0].description = 'Здесь вы можете купить свитки'
            for i in slots:
                if i['type'] == 'scroll':
                    all.append(i)

            for i in all:
                interaction.message.embeds[0].add_field(name=f"{i['lvl']}lvl - {i['name']} - {i['price']}<:silver"
                                                             f":997889161484828826> ",
                                                        value=i["description"], inline=False)

            if len(interaction.message.embeds[0].fields) == 0:
                interaction.message.embeds[0].description = 'Здесь вы можете купить свитки, но пока тут ничего нет, ' \
                                                            'загляните позже '

            await interaction.response.edit_message(embed=interaction.message.embeds[0])

        elif self.values[0] == 'Зелья':

            interaction.message.embeds[0].title = 'Зелья'
            interaction.message.embeds[0].description = 'Здесь вы можете купить зелья'

            for i in slots:
                if i['type'] == 'potion':
                    all.append(i)

            for i in all:
                interaction.message.embeds[0].add_field(name=f"{i['lvl']}lvl - {i['name']} - {i['price']}<:silver"
                                                             f":997889161484828826> ",
                                                        value=i["description"], inline=False)

            if len(interaction.message.embeds[0].fields) == 0:
                interaction.message.embeds[0].description = 'Здесь вы можете купить зелья, но пока тут ничего нет, ' \
                                                            'загляните позже '

            await interaction.response.edit_message(embed=interaction.message.embeds[0])

        else:
            interaction.message.embeds[0].title = 'Обмундирование'
            interaction.message.embeds[0].description = 'Здесь вы можете купить обмундерование'

            for i in slots:
                if i['type'] != 'potion' and i['type'] != 'scroll':
                    all.append(i)

            for i in all:
                interaction.message.embeds[0].add_field(name=f"{i['lvl']}lvl - {i['name']} - {i['price']}<:silver"
                                                             f":997889161484828826> ",
                                                        value=i["description"], inline=False)

            await interaction.response.edit_message(embed=interaction.message.embeds[0])


class Shopper(commands.Cog):
    def __init__(self, bot):
        global users_db, info_db
        self.bot = bot

    @app_commands.command(name="shop", description="посмотреть ассортимент магазина")
    async def shop(self, interaction: discord.Interaction):
        await checker.check(interaction)
        emb = discord.Embed(title=f'Магазин', description="Выберете вам нужное меню для покупки")
        view = discord.ui.View(timeout=180).add_item(Dropdown(self.bot))
        await interaction.response.send_message(embed=emb, view=view)

    @app_commands.command(name="buy", description="преобрести товар")
    @app_commands.describe(name = "Название товара из магазина. Если название имеет ковычки, то прописывать и их",
                           amount = "Количество товара которое вы хотите купить")
    async def buy(self, interaction: discord.Interaction, name: str, amount: int = 1):
        await checker.check(interaction)
        items = info_db.find_one({"_id": "shop"})["items"]
        item = None

        if amount < 1:
            await interaction.response.send_message(embed=checker.err_embed(f"Вы не можете купить меньше 1 предмета")
                                                    ,ephemeral=True)
            return

        for i in items:
            if i["name"].lower().replace(" ", "") == name.lower().replace(" ", ""):
                item = i

        if item is None:
            await interaction.response.send_message(embed=checker.err_embed("Такого предмета нет в магазине")
                                                    , ephemeral=True)
            return

        item = item_db.find_one({"_id": item["_id"]}) or None

        if item is None:
            await interaction.response.send_message(embed=checker.err_embed("Такого предмета нет в магазине")
                                                    , ephemeral=True)
            return

        us_info = users_db.find_one({"_id": interaction.user.id})

        if us_info["cash"] < item["price"] * amount:
            await interaction.response.send_message(embed=checker.err_embed("У вас недостаточно денег"), ephemeral=True)
            return

        if us_info['lvl'] < item['lvl']:
            await interaction.response.send_message(embed=checker.err_embed("У вас слишком низкий уровень для "
                                                                            "покупки данного предмета"),
                                                    ephemeral=True)
            return

        if us_info['inventory'].__len__() + amount > 30:
            await interaction.response.send_message(embed=checker.err_embed("У вас недостаточно места в инвентаре"
                                                                            " для пребретения этого "
                                                    "товара в таком количестве"), ephemeral=True)
            return

        users_db.update_one({"_id": interaction.user.id}, {"$set": {"cash": us_info["cash"] - item["price"] * amount}})

        for i in range(amount):
            users_db.update_one({"_id": interaction.user.id}, {"$push": {"inventory": item["_id"]}})

        await interaction.response.send_message(embed=checker.emp_embed(f"✅ Вы успешно преобрели \"{item['name']}\" "
                                                                        f"в количестве {amount}шт. потратив"
                                                f"{amount*item['price']}<:silver:997889161484828826>"), ephemeral=True)

