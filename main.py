import datetime
import discord
import pymongo
from discord import app_commands
from discord.ext import commands
from modules import checker
import traceback
from dotenv import load_dotenv
import os
from modules.client import CustomClient

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")
MONGO_KEY = os.environ.get("MONGO_KEY")


bot = CustomClient(MONGO_KEY)


@app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id)
@app_commands.checks.bot_has_permissions(moderate_members=True)
@bot.tree.command(name="проклятие", description="Мьютит участника на 10 минут")
async def aboba(interaction: discord.Interaction, member: discord.Member):
    await checker.check(interaction)

    if not bot.servers_db.find_one({"_id": interaction.guild_id})['m_scroll']:
        await interaction.response.send_message(embed=checker.err_embed('На данном сервере запрещено '
                                                                        'использовать проклятия'),
                                                ephemeral=True)
        return

    top_role = member.top_role
    biba = interaction.guild.get_member(bot.user.id)
    bot_top_role = biba.top_role
    if top_role.position > bot_top_role.position:
        await interaction.response.send_message(embed=checker.err_embed(f"Моя роль ниже, чем {member.mention}"
                                                                        f", я не могу его мьютить"),
                                                ephemeral=True)
        return

    atk = users_db.find_one({"_id": interaction.user.id})['inventory']

    if 'a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9' not in atk:
        await interaction.response.send_message(embed=checker.err_embed('У вас нет свитка "Проклятие"'), ephemeral=True)
        return

    def_ = users_db.find_one({"_id": member.id})['inventory'] or None
    if def_ is not None:
        if '7f12ec8e-71b9-4c11-8d2c-8c26fcf0db6c' in def_:
            await interaction.response.send_message(embed=checker.emp_embed(f'У {member.mention} был свиток "Защиты"'
                                                                            f', оба свитка сгорели'))
            def_.remove('7f12ec8e-71b9-4c11-8d2c-8c26fcf0db6c')
            atk.remove('a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9')
            users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": atk}})
            users_db.update_one({"_id": member.id}, {"$set": {"inventory": def_}})
            return

    atk.remove('a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9')
    users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": atk}})
    await interaction.response.send_message(embed=checker.emp_embed('Проклятие успешно сработало на ' + member.mention))

    await member.edit(timed_out_until=discord.utils.utcnow() + datetime.timedelta(minutes=10),
                      reason=f'Вы замьючены: {interaction.user.id} на 10 минут')


# @bot.tree.error
# async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
#     if isinstance(error, app_commands.CommandOnCooldown):
#         await interaction.response.send_message(embed=checker.err_embed(
#             f"Не так быстро. Вы сможете повторно использовать эту команду через {error.retry_after:.2f} секунд"),
#             ephemeral=True)
#
#     elif isinstance(error, app_commands.BotMissingPermissions):
#         await interaction.response.send_message(embed=checker.err_embed(
#             f"Я не могу выполнить эту команду, потому что я не имею необходимых прав, а именно: "
#             f"`{' '.join(error.missing_permissions)}`"), ephemeral=True)
#
#     elif isinstance(error, app_commands.MissingPermissions):
#         await interaction.response.send_message(
#             embed=checker.err_embed(f"У вас недостаточно прав для использования данной "
#                                     f"команды, требуемые права: "
#                                     f"`{' '.join(error.missing_permissions)}`"), ephemeral=True)
#
#
#     elif isinstance(error, discord.InteractionResponded):
#         return
#
#     elif isinstance(error, discord.NotFound):
#         return
#
#     else:
#         await interaction.response.send_message("Произошла какая-то ошибка, попробуйте позже", ephemeral=True)
#         print(error)


@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return

    if ctx.content.startswith(f'<@!{bot.user.id}>') or ctx.content.startswith(f'<@{bot.user.id}>'):
        emb = discord.Embed(title=f"**{bot.user.name}**")
        emb.add_field(name=f"**Привет! Я бот {bot.user.name}! Я являюсь игрой в жанре RPG.**",
                      value="Блогодоря мне вы можете ходить в походы, прокачивать персонажа, выбивать предметы с "
                            "монстров... короче почти всё что есть в обычной  RPG 🤗\n\n "
                            f"**Если возникли технические шоколадки, либо нужна помощь,свяжитесь с нами на "
                            f"официальном сервере поддержки "
                            f"бота:** [Официальный сервер бота](https://discord.gg/eZKrFTv7D8)\n"
                            f"Так же в нашу команду требуются художники и кодеры, так что будем рады любой помощи 😘"
                      # f"[Поддержка автора](https://www.donationalerts.com/r/neznakomec_)"
                      )
        aba = await bot.fetch_user(426986442632462347)
        emb.set_footer(text=aba.name + "#" + aba.discriminator + " ©", icon_url=aba.avatar.url)

        await ctx.send(embed=emb)

        return

    await bot.process_commands(ctx)


def load_cogs(debug=False):
    """Загрузка когов"""
    for filename in os.listdir("./cogs"):
        if not filename.endswith(".py"):
            continue
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
        except Exception as error:
            print(f'{filename[:-3]}: крашнут')
            if debug:
                print(traceback.format_exc())
        else:
            print(f"{filename[:-3]}: включён")
    print("=" * 20)


@bot.event
async def on_ready():
    load_cogs(debug=True)
    await bot.tree.sync()
    print(f"Бот онлайн\nИмя: {bot.user.name}\nid: {bot.user.id}\n")


if __name__ == "__main__":
    bot.run(TOKEN)
