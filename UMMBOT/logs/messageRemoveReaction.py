from discord.ext import commands
import discord
import sqlite3

from constants import Guild_Info

from embed.logs.embedRReaction import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventMessageAddReaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):

        if user.bot:
            return

        message = reaction.message
        if message.type != discord.MessageType.default:
            return

        channel = message.channel
        if channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                            discord.ChannelType.store]:
            return

        guild = channel.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Logs.remove_react
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
            WHERE Guild.id = ? AND Channel.logs_message = 1
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

        cursor.execute("""
        SELECT Channel.id
        FROM Channel
        INNER JOIN Guild
        ON Channel.guild_id = Guild.id
        WHERE Guild.id = ?
        GROUP BY Channel.id
        HAVING logs_admin = 1 OR logs_voice = 1 OR logs_sanction = 1 OR logs_message = 1
        ;
        """, (guild.id,))

        logs_channels = cursor.fetchall()[0]

        if channel.id not in logs_channels:
            embed = Embed(reaction, user, message)
            embed = await embed.reaction_remove()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventMessageAddReaction(client))
