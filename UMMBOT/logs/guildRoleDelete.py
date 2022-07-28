from discord.ext import commands
import sqlite3

from constants import Guild_Info


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventGuildMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        guild = role.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        DELETE FROM Role
        WHERE id = ? and guild_id = ?
        ;
        """, (role.id, guild.id))
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventGuildMemberJoin(client))
