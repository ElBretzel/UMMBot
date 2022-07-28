from discord.ext import commands
from discord import Intents
import os
import sys
import glob

from utils.sql.guild_leave import leave_guild
from utils.sql.new_guild import new_guild
from utils.sql.create_database import create_database

from constants import PREFIX, OWNER, DIRECTORY, OS_SLASH

from utils.checking.bot_start_check_sanction import checkup

sys.path.insert(1, os.path.join(os.getcwd(), "utils"))
os.chdir(DIRECTORY)

TOKEN = ""
INVITE = "https://discord.com/oauth2/authorize?client_id=677213520529457152&scope=bot&permissions=8"

default_intents = Intents.default()
default_intents.members = True
default_intents.typing = False
default_intents.presences = False


class UMMBot(commands.Bot):
    def __init__(self):
        self.PREFIX = PREFIX
        super().__init__(command_prefix=PREFIX, intents=default_intents, reconnect=True)

    def load_logs(self):
        logs_file = glob.iglob(f"logs{OS_SLASH}**.py")
        for files in logs_file:
            print(files)
            files = files.split(f"{OS_SLASH}")[1][:-3]
            print(f"Lancement du module {files}")

            self.load_extension(f'logs.{files}')

    def load_commands(self):
        cogs_file = glob.iglob(f"cogs{OS_SLASH}**.py")
        for files in cogs_file:
            files = files.split(f"{OS_SLASH}")[1][:-3]
            print(f"Lancement du module {files}")
            self.load_extension(f'cogs.{files}')

    def start_bot(self, token):
        print("Vérification de la base de donnée...")
        create_database()
        print("\nSuppression de la commande help...")
        self.remove_command('help')
        print("Effectué!")
        print("\nGénération des modules logs...")
        self.load_logs()
        print("\nGénération des modules commandes...")
        self.load_commands()
        print("\nLancement du bot...")
        self.run(token)

    async def on_ready(self):
        print("UMMBOT est prêt!")
        print(f"Lien d'invitation: {INVITE}\n")

        print("Pour inviter UMMBot, veillez copier ce lien et mettre au bot la permission administrateur.")
        print("Une fois rejoint, veillez déplacer le rôle UMMBot tout en haut de la liste des rôles.")
        print(f"En cas de problème, veillez contacter {OWNER}.")
        await checkup(self)

    async def on_guild_join(self, guild):
        print(f"New guild ! {guild.id}")
        new_guild(guild)

    async def on_guild_remove(self, guild):
        leave_guild(guild)


bot = UMMBot()
bot.start_bot(TOKEN)

# discord.py[voice]
# pytz
# from discord.ext import commands
# pyspellchecker
# emoji
