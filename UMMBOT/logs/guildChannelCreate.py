from discord.ext import commands
import sqlite3

from constants import Guild_Info

import discord


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventGuildMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                            discord.ChannelType.store]:
            return

        guild = channel.guild

        if guild.id not in Guild_Info.umm_whitelist:
            return

        channel_type = str(channel.type)

        if channel_type == "text":
            channel_type = "TXT"

        elif channel_type == "voice":
            channel_type = "VOC"

        elif channel_type == "category":
            channel_type = "CAT"

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        INSERT INTO Channel ( id, guild_id, type )
        VALUES ( ?, ?, ? )
        ;
        """, (channel.id, guild.id, channel_type))
        connexion.commit()

        if channel_type == "CAT":
            cursor.execute("""
            INSERT INTO Category_Channel ( id )
            VALUES ( ? )
            ;
            """, (channel.id,))
        elif channel_type == "TXT":
            cursor.execute("""
            INSERT INTO Text_Channel ( id )
            VALUES ( ? )
            ;
            """, (channel.id,))
        elif channel_type == "VOC":
            cursor.execute("""
            INSERT INTO Vocal_Channel ( id )
            VALUES ( ? )
            ;
            """, (channel.id,))
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventGuildMemberJoin(client))
