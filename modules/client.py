import discord
import pymongo
from discord.ext import commands


class CustomClient(commands.Bot):
    def __init__(self, mongo_key: str, /):
        super().__init__(command_prefix="%%%", intents=discord.Intents.default())
        cluster = pymongo.MongoClient(mongo_key)
        db = cluster["MMORPG"]

        self.users_db = db["users"]
        self.servers_db = db["servers"]
        self.info_db = db["info"]
        self.items_db = db["items"]
