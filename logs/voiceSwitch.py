import discord
from discord.ext import commands
import sqlite3

from constants import VoiceState, Guild_Info

from embed.logs.embedVSwitch import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class UserSwitch(commands.Cog):
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
        SELECT Logs.voice_switch
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
        if (voice_before["mute"] != voice_after["mute"]) or (voice_before["deaf"] != voice_after["deaf"]):
            close_connexion(connexion)
            return
        if (voice_before["self_mute"] != voice_after["self_mute"]) or (voice_before["self_deaf"] != voice_after["self_deaf"]):
            close_connexion(connexion)
            return

        if after.channel.name == "kick":
            close_connexion(connexion)
            return

        cursor.execute("""
        SELECT Entry.entry_m_id, Entry.m_number
        FROM Entry
        WHERE id = ?
        ;
        """, (guild.id,))

        entry_result = cursor.fetchall()[0]

        entry_id = entry_result[0]
        entry_number = [int(i) for i in entry_result[1].split(" ")]

        entry = None
        entries = []
        async for entry in guild.audit_logs(limit=10,
                                            action=discord.AuditLogAction.member_move):
            entries.append(entry)

        if entry:

            for n, entry_num in enumerate(entry_number):
                entry_count = entries[n].extra.count

                if entry_id == 0 or entries[n].user.id == member.id:
                    continue

                if n == 0 and entry_id != entries[n].id:
                    result = entries[n].user
                    break

                elif entry_count == entry_num + 1:
                    result = entries[n].user
                    break
            else:
                result = False

            last_entry_id = entries[0].id
            last_entry_count = ' '.join([str(i.extra.count) for i in entries])
            cursor.execute("""
            UPDATE Entry
            SET entry_m_id = ?, m_number = ?
            WHERE id = ?
            ;
            """, (last_entry_id, last_entry_count, guild.id))
            connexion.commit()
        else:
            result = False

        if not isinstance(result, bool):
            if result.bot:
                close_connexion(connexion)
                return

            embed = Embed(member, before.channel, after.channel, result)
            embed = await embed.mod_switch()
            channel_send = self.client.get_channel(log_channel_id)

        else:
            embed = Embed(member, before.channel, after.channel)
            channel_send = self.client.get_channel(log_channel_id)
            embed = await embed.user_switch()

        await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(UserSwitch(client))
