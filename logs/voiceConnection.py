from discord.ext import commands
import discord
import sqlite3

from constants import Guild_Info

from embed.logs.embedVConnection import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class UserConnect(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if member.bot:
            return

        guild = member.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Logs.voice_connect
        FROM Logs
        INNER JOIN Guild
        ON Logs.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        log_authorization = cursor.fetchall()[0][0]

        if log_authorization:

            cursor.execute("""
            SELECT Channel.id
            FROM Channel
            INNER JOIN Guild
            ON Channel.guild_id = Guild.id
            WHERE Guild.id = ? AND Channel.logs_voice = 1
            ;
            """, (guild.id,))
            log_channel_id = cursor.fetchall()
            log_channel_id = False if not log_channel_id else log_channel_id[0][0]
            if not log_channel_id:
                close_connexion(connexion)
                return
        else:
            close_connexion(connexion)
            return

        if isinstance(before.channel, type(None)):

            if after.channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                                      discord.ChannelType.store]:
                return

            cursor.execute("""
            SELECT Vocal_Channel.generator
            FROM Vocal_Channel
            INNER JOIN Channel
            ON Vocal_Channel.id = Channel.id
            INNER JOIN Guild
            ON Channel.guild_id = Guild.id
            WHERE Channel.id = ? AND Guild.id = ? AND Vocal_Channel.generator = 1
            ;
            """, (after.channel.id, guild.id))

            private_channel = cursor.fetchall()

            if private_channel:
                print("")
                # await PrivateChannel(self.client, member, before_channel, after_channel).voice_connect()
            connect = True

        elif isinstance(after.channel, type(None)):

            if before.channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                                       discord.ChannelType.store]:
                return

            if before.channel.name == "kick":
                close_connexion(connexion)
                return

            cursor.execute("""
            SELECT Private_Channel.id
            FROM Private_Channel
            INNER JOIN Member
            ON Private_Channel.id = Member.id
            INNER JOIN Guild
            ON Member.guild_id = Guild.id
            WHERE Guild.id = ? AND Private_Channel.id_voice = ?
            ;
            """, (before.channel.id, guild.id))

            private_channel = cursor.fetchall()
            if private_channel:
                print("")
                # await PrivateChannel(self.client, member, before_channel, after_channel).voice_disconnect()
            connect = False

        else:
            close_connexion(connexion)
            return

        if connect:
            embed = Embed(member, after.channel)
            embed = await embed.voice_connect()
        else:
            embed = Embed(member, before.channel)
            embed = await embed.voice_disconnect()

        channel_send = self.client.get_channel(log_channel_id)
        await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(UserConnect(client))
