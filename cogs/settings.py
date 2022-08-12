import discord
from discord import app_commands
from discord.ext import commands

from modules import checker


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="свитки", description="Разрешает/запрещает использование свитка проклятья на сервере")
    @app_commands.choices(arg=[app_commands.Choice(name="on", value=1),
                               app_commands.Choice(name="off", value=0)])
    @app_commands.describe(arg="0n - разрешить использование свитков, 0ff - запретить использование свитков")
    async def scroll(self, interaction: discord.Interaction, arg: int):
        self.bot.servers_db.update_one({"_id": interaction.guild_id}, {"$set": {"m_scroll": bool(arg)}})
        if arg == 1:
            await interaction.response.send_message(
                embed=checker.emp_embed(
                    "Свиток \"Проклятие\" включен\n⚠️Убедитесь что у бота есть право `Moderate Members` для "
                    "выдачи таймаутов"))

        else:
            await interaction.response.send_message(embed=checker.emp_embed("Свиток \"Проклятие\" выключен"))

    @app_commands.command(name="info", description="Информация о боте")
    async def info(self, interaction: discord.Interaction):
        await checker.check(self.bot, interaction)
        emb = discord.Embed(title=f"**{self.bot.user.name}**")
        emb.add_field(name=f"**Привет! Я бот {self.bot.user.name}! Я являюсь игрой в жанре RPG.**",
                      value="Блогодоря мне вы можете ходить в походы, прокачивать персонажа, выбивать предметы с "
                            "монстров... короче почти всё, что можно делать в обычной  RPG 🤗\n\n "
                            f"**Если возникли технические шоколадки, либо нужна помощь,свяжитесь с нами на "
                            f"официальном сервере поддержки "
                            f"бота:** [Официальный сервер бота](https://discord.gg/eZKrFTv7D8)\n"
                            f"Так же в нашу команду требуются художники и кодеры, так что будем рады любой помощи 😘"
                      # f"[Поддержка автора](https://www.donationalerts.com/r/neznakomec_)"
                      )
        aba = await self.bot.fetch_user(426986442632462347)
        emb.set_footer(text=aba.name + "#" + aba.discriminator + " ©", icon_url=aba.avatar.url)

        await interaction.response.send_message(embed=emb)


async def setup(client):
    await client.add_cog(Settings(client))
