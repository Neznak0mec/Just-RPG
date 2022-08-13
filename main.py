import datetime
import os
import traceback

import discord
from discord import app_commands
from dotenv import load_dotenv

from modules import checker
from modules.client import CustomClient
from settings import DEFEND_SCROLL_ID, bcolors

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
    await checker.check(bot,interaction)

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

    atk = bot.users_db.find_one({"_id": interaction.user.id})['inventory']

    if 'a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9' not in atk:
        await interaction.response.send_message(embed=checker.err_embed('У вас нет свитка "Проклятие"'), ephemeral=True)
        return

    def_ = bot.users_db.find_one({"_id": member.id})['inventory'] or None
    if def_ is not None:
        if DEFEND_SCROLL_ID in def_:
            await interaction.response.send_message(embed=checker.emp_embed(f'У {member.mention} был свиток "Защиты"'
                                                                            f', оба свитка сгорели'))
            def_.remove(DEFEND_SCROLL_ID)
            atk.remove('a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9')
            bot.users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": atk}})
            bot.users_db.update_one({"_id": member.id}, {"$set": {"inventory": def_}})
            return

    atk.remove('a3840ab0-9e1e-49d7-bb03-19b49d3e0cd9')
    bot.users_db.update_one({"_id": interaction.user.id}, {"$set": {"inventory": atk}})
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



async def load_cogs(debug=False):
    """Загрузка когов"""
    for filename in os.listdir("./cogs"):
        if not filename.endswith(".py"):
            continue
        try:
            await bot.load_extension(f"cogs.{filename[:-3]}")
        except Exception as error:
            print(bcolors.FAIL+f'{filename[:-3]}: крашнут'+bcolors.ENDC)
            if debug:
                print(traceback.format_exc())
        else:
            print(bcolors.OKGREEN+f"{filename[:-3]}: включён"+bcolors.ENDC)
    print("=" * 20)


@bot.event
async def on_ready():
    await load_cogs(debug=True)
    await bot.tree.sync()
    print(f"Бот онлайн\nИмя: {bot.user.name}\nid: {bot.user.id}\n")


if __name__ == "__main__":
    bot.run(TOKEN)
#     todo: заметить в бд helem на helmet
#     todo: заметить в бд heal на hp
