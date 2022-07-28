from discord.ext import commands
import asyncio
import sqlite3
from datetime import datetime
import pytz

from rules.badwordsMessage import CheckBadWords
from rules.linkMessage import DetectLink

from utils.action.converter import time_reason
from utils.action.timed_mute import TimeMute

from embed.logs.embedMJoin import Embed
from embed.logs.embedQuitAndMute import EmbedMute

from constants import Guild_Info, Infraction


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventGuildMemberJoin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.bot:
            return

        guild = member.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        INSERT INTO Member ( member_id, guild_id )
        VALUES ( ?, ? );
        """, (member.id, guild.id))

        connexion.commit()

        cursor.execute("""
        SELECT Logs.member_join
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
            WHERE Guild.id = ? AND Channel.logs_admin = 1
            ;
            """, (guild.id,))
            log_channel_id = cursor.fetchall()
            log_channel_id = None if not log_channel_id else log_channel_id[0][0]
        else:
            log_channel_id = None

        if member.id != guild.owner.id and log_channel_id:

            embed = Embed(member).new_member()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

            tasks = [CheckBadWords, DetectLink]
            tasks = tuple(t(self.client, member.name, guild) for t in tasks)
            func = [tasks[0].spellcheck, tasks[1].message_link]

            results = await asyncio.gather(*func)

            for index, result in enumerate(results):
                if result:
                    await tasks[index].rule_break(member, None, log_channel_id, result, "u")
                    break

        cursor.execute("""
        SELECT sanction_finish, sanction_type, Sanction.id
        FROM Sanction
        INNER JOIN Guild
        ON Guild.id = guild_id
        WHERE Guild.id = ? AND sanction_user_id = ? AND (sanction_type = 'MUTE' OR sanction_type = 'VMUTE' OR sanction_type = 'GMUTE') AND punished = 0
        ORDER BY Sanction.id DESC
        LIMIT 1
        """, (guild.id, member.id))
        sanction_finish = cursor.fetchone()

        cursor.execute("""
        SELECT Channel.id
        FROM Channel
        INNER JOIN Guild
        ON Channel.guild_id = Guild.id
        WHERE Guild.id = ? AND Channel.logs_sanction = 1
        ;
        """, (guild.id,))
        log_channel_id = cursor.fetchall()
        log_channel_id = None if not log_channel_id else log_channel_id[0][0]

        close_connexion(connexion)

        tz = pytz.timezone('Europe/Paris')
        if sanction_finish:
            sanction_time = datetime.strptime(sanction_finish[0], "%Y-%m-%d %H:%M:%S").astimezone(tz)
            date = datetime.now(tz)

            if date < sanction_time:
                difference = sanction_time - date
                timereason = await time_reason(difference.total_seconds())

                if log_channel_id:
                    if sanction_finish[1] == "MUTE":
                        embed = await EmbedMute(member, timereason, sanction_finish[2]).member_mute(Infraction.mute.value)
                    elif sanction_finish[1] == "VMUTE":
                        embed = await EmbedMute(member, timereason, sanction_finish[2]).member_vmute(Infraction.vmute.value)
                    elif sanction_finish[1] == "GMUTE":
                        embed = await EmbedMute(member, timereason, sanction_finish[2]).member_gmute(Infraction.gmute.value)
                    channel_send = self.client.get_channel(log_channel_id)
                    await channel_send.send(embed=embed)

                await TimeMute().mute(member, difference.total_seconds(), sanction_finish[1])


def setup(client):
    client.add_cog(EventGuildMemberJoin(client))
