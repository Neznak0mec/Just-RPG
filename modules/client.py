import discord
import pymongo
from discord.ext import commands


class CustomClient(commands.Bot):
    def __init__(self, mongo_key: str, /):
        super().__init__(command_prefix="%%%", intents=discord.Intents.all())
        cluster = pymongo.MongoClient(mongo_key)
        db = cluster["MMORPG"]

        self.users_db = db["users"]
        self.servers_db = db["servers"]
        self.info_db = db["info"]
        self.items_db = db["items"]

    # async def get_responce(self, user_id: int, channel_id: int, message_id: int, types: list, timeout: int = 300):
    #     """Ждет нажатия на кнопку, или взаимодействия с селект меню.
    #     Варианты событий ["button", "dropdown", "message"]"""
    #
    #     def check_drop_and_mes(res):
    #         return user_id == res.user.id and res.channel.id == channel_id and res.message.id == message_id
    #
    #     def check_mes(msg):
    #         return user_id == msg.author.id and msg.channel.id == channel_id
    #
    #     tasks = []
    #     if "button" in types:
    #         tasks.append(asyncio.create_task(
    #             self.wait_for('button_click', check=check_drop_and_mes),
    #             name="button")
    #         )
    #     if "dropdown" in types:
    #         tasks.append(asyncio.create_task(
    #             self.wait_for('dropdown', check=check_drop_and_mes),
    #             name="dropdown")
    #         )
    #     if "message" in types:
    #         tasks.append(asyncio.create_task(
    #             self.wait_for('message', check=check_mes),
    #             name="message")
    #         )
    #
    #     try:
    #         done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED,
    #                                            timeout=timeout)
    #     except asyncio.TimeoutError:
    #         return None, None
    #     if not list(done):
    #         return None, None
    #     finished: asyncio.Task = list(done)[0]
    #     for task in pending:
    #         try:
    #             task.cancel()
    #         except:
    #             pass
    #     return finished.get_name(), finished.result()

    # async def test(self):
    #     embed = disnake.Embed()
    #     view = disnake.ui.View()
    #     view.add_item(Button(style=ButtonStyle.green, label='Войти', row=0, custom_id="enter"))
    #     view.add_item(Button(style=ButtonStyle.red, label='Остаться', row=0, custom_id="cancel"))
    #     await inter.send(embed=embed, view=view)
    #     msg = await inter.original_message()
    #     action_type, response = await self.get_responce(
    #         user_id=inter.author.id,
    #         channel_id=inter.channel_id,
    #         message_id=msg.id,
    #         types=["button"]
    #     )
    #     if not response:
    #         return
    #     elif response.component.custom_id == 'cancel':
    #         return
