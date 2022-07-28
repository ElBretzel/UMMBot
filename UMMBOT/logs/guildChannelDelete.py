from discord.ext import commands
import sqlite3
import discord

from constants import Guild_Info


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventGuildMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        if channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                       discord.ChannelType.store]:
            return

        guild = channel.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        PRAGMA foreign_keys = ON
        ;
        """)
        connexion.commit()

        cursor.execute("""
        DELETE FROM Channel
        WHERE id = ? AND guild_id = ?
        ;
        """, (channel.id, guild.id))
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventGuildMemberJoin(client))
