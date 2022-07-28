from discord.ext import commands
import discord
import sqlite3

from constants import VoiceState, Guild_Info

from embed.logs.embedVSUpdate import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class UserStateUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if member.bot:
            return

        guild = member.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        if any([isinstance(before.channel, type(None)), isinstance(after.channel, type(None))]):
            return

        if before.channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                                   discord.ChannelType.store]:
            return

        if after.channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                                  discord.ChannelType.store]:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Logs.voice_selfupdate
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

        voice_before, voice_after = VoiceState.voicestate(before), VoiceState.voicestate(after)
        if (voice_before["self_mute"] == voice_after["self_mute"]) and (voice_before["self_deaf"] == voice_after["self_deaf"]):
            close_connexion(connexion)
            return

        if (voice_before["mute"] != voice_after["mute"]) or (voice_before["deaf"] != voice_after["deaf"]):
            close_connexion(connexion)
            return

        if voice_before["self_mute"] != voice_after["self_mute"] and voice_before["self_deaf"] == voice_after["self_deaf"]:
            if not voice_before["self_mute"] and voice_after["self_mute"]:
                state = "MUTE"
                activate = False
            elif voice_before["self_mute"] and not voice_after["self_mute"]:
                state = "UNMUTE"
                activate = True
            embed = Embed(member, after.channel, state)
        elif voice_before["self_deaf"] != voice_after["self_deaf"]:
            if not voice_before["self_deaf"] and voice_after["self_deaf"]:
                state = "SOURDINE"
                activate = False
            elif voice_before["self_deaf"] and not voice_after["self_deaf"]:
                state = "NON SOURDINE"
                activate = True
            embed = Embed(member, after.channel, state)
        else:
            close_connexion(connexion)
            return

        embed = await embed.voice_on() if activate else await embed.voice_off()
        channel_send = self.client.get_channel(log_channel_id)
        await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(UserStateUpdate(client))
