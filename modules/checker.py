import datetime

import discord
import pymongo


def get_time(oba: datetime.datetime):
    mass = [oba.year, oba.month, oba.day, oba.hour, oba.minute, oba.second]
    sotr = ""
    for i in mass:
        if i < 10:
            i = "0" + str(i)

        sotr += str(i)

    return sotr


async def check(bot, interaction: discord.Interaction):
    if bot.users_db.count_documents({"_id": interaction.user.id}) == 0:
        post = {
            "_id": interaction.user.id,
            "cash": 0,
            "cooldown": get_time(datetime.datetime.now()),
            "lvl": 1,
            "exp": 0,
            "exp_to_lvl": 100,
            "skill_points": 0,
            "heal": 100,
            "damage": 1,
            "defence": 1,
            "speed": 1,
            "krit": 1,
            "luck": 1,
            "equipment":
                {
                    "helem": None,
                    "armor": None,
                    "pants": None,
                    "shoes": None,
                    "gloves": None,
                    "weapon": None
                },
            "inventory": [],
        }
        bot.users_db.insert_one(post)

    if bot.servers_db.count_documents({"_id": interaction.guild_id}) == 0:
        post = {
            "_id": interaction.guild_id,
            "m_scroll": False,
            "language": "ru"
        }
        bot.servers_db.insert_one(post)


def err_embed(text: str):
    return discord.Embed(title="🚫 Ошибка", description=text)


def emp_embed(text: str):
    return discord.Embed(description=text)
