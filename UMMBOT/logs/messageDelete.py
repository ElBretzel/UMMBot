import discord
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import pytz

from constants import Guild_Info

from embed.logs.embedMDelete import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventMessageDelete(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if message.type != discord.MessageType.default:
            return

        member = message.author
        if member.bot:
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
        SELECT Logs.message_delete
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
            log_channel_id_msg = cursor.fetchall()
            log_channel_id_msg = False if not log_channel_id_msg else log_channel_id_msg[0][0]

            cursor.execute("""
            SELECT Channel.id
            FROM Channel
            INNER JOIN Guild
            ON Channel.guild_id = Guild.id
            WHERE Guild.id = ? AND Channel.logs_admin = 1
            ;
            """, (guild.id,))
            log_channel_id_admin = cursor.fetchall()
            log_channel_id_admin = False if not log_channel_id_admin else log_channel_id_admin[0][0]
            if not log_channel_id_msg and not log_channel_id_admin:
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

        if channel.id in logs_channels:
            close_connexion(connexion)
            return

        entries = []
        entry = None
        async for entry in guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=10):
            entries.append(entry)

        if entry:

            cursor.execute("""
            SELECT Mod_Action.timestamp, Mod_Action.user_id
            FROM Mod_Action
            INNER JOIN Guild
            ON Mod_Action.guild_id = Guild.id
            WHERE Guild.id = ? AND Mod_Action.user_id = ? AND Mod_Action.action_ = 'DELETE' AND Mod_Action.type = 'BOT'
            ORDER BY Mod_Action.timestamp DESC
            LIMIT 1
            ;
            """, (guild.id, member.id))

            mod_action = cursor.fetchall()
            tz = pytz.timezone('Europe/Paris')
            if mod_action:
                mod_action = mod_action[0]
                mod_action_time = datetime.fromisoformat(mod_action[0])
            else:
                mod_action_time = datetime.fromisoformat('2011-11-04')
            mod_action_time = mod_action_time.astimezone(tz)

            cursor.execute("""
            SELECT Entry.entry_d_id, Entry.d_number
            FROM Entry
            WHERE id = ?
            ;
            """, (guild.id,))

            entry_result = cursor.fetchall()[0]
            entry_id = entry_result[0]
            entry_number = [int(i) for i in entry_result[1].split(" ")]

            for n, entry_num in enumerate(entry_number):
                entry_count = entries[n].extra.count

                if entry_id == 0:
                    continue

                if datetime.now(tz) - timedelta(seconds=5) <= mod_action_time <= datetime.now(tz) + timedelta(seconds=5) and\
                        member.id == mod_action[1]:
                    print("messageDelete.py -> Bot delete")
                    cursor.execute("""DELETE FROM Mod_Action
                                      WHERE guild_id = ? AND user_id = ? AND action_ = 'DELETE'
                                      AND type = 'BOT' AND timestamp = ?;""", (guild.id, member.id, mod_action[0]))
                    close_connexion(connexion)
                    return

                elif entries[n].user.id == member.id:
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
            SET entry_d_id = ?, d_number = ?
            WHERE id = ?
            ;
            """, (last_entry_id, last_entry_count, guild.id))
            connexion.commit()

        else:
            result = False

        if result:
            if not log_channel_id_admin:
                close_connexion(connexion)
                return
            embed = Embed(member, channel, message, result)
            embed = await embed.mod_delete()
            channel_send = self.client.get_channel(log_channel_id_admin)

        else:
            if not log_channel_id_msg:
                close_connexion(connexion)
                return
            embed = Embed(member, channel, message)
            channel_send = self.client.get_channel(log_channel_id_msg)
            embed = await embed.user_delete()

        await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventMessageDelete(client))
