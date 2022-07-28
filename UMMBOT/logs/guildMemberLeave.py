import discord
from discord.ext import commands
import sqlite3
import pytz
from datetime import timedelta, datetime

from constants import Guild_Info

from embed.logs.embedMLeave import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventGuildMemberLeave(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if member.bot:
            return

        guild = member.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        DELETE FROM Member
        WHERE Member.member_id = ? AND Member.guild_id IN (
        SELECT Guild.id
        FROM Guild
        WHERE Guild.id = ?
        )
        """, (member.id, guild.id))
        connexion.commit()

        tz = pytz.timezone('Europe/Paris')
        init_time = datetime.now(tz)

        sanction_kick = False
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1).filter(
                lambda m: m.target.id == member.id and m.user.id != member.id):

            entry_creation = entry.created_at.replace(tzinfo=pytz.utc)
            entry_creation = entry_creation.astimezone(tz)

            if entry_creation - timedelta(seconds=3) <= init_time <= entry_creation + timedelta(seconds=3):
                sanction_kick = True
                mod_user = entry.user

        sanction_ban = False
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1).filter(
                lambda m: m.target.id == member.id and m.user.id != member.id):

            entry_creation = entry.created_at.replace(tzinfo=pytz.utc)
            entry_creation = entry_creation.astimezone(tz)

            if entry_creation - timedelta(seconds=3) <= init_time <= entry_creation + timedelta(seconds=3):
                sanction_ban = True
                mod_user = entry.user

        if sanction_kick or sanction_ban:

            cursor.execute("""
            UPDATE Sanction
            SET punished = 1
            WHERE Sanction.id IN (SELECT Sanction.id
            FROM Sanction
            WHERE Sanction.guild_id = ? AND sanction_user_id = ? AND (sanction_type = 'MUTE' OR sanction_type = 'VMUTE' OR sanction_type = 'GMUTE') AND punished = 0
            ORDER BY Sanction.id DESC
            LIMIT 1)
            """, (guild.id, member.id))
            connexion.commit()

            if mod_user.bot:
                close_connexion(connexion)
                return

            embed = Embed(member, mod_user)
            if sanction_kick:
                embed = await embed.member_kick()
            else:
                embed = await embed.member_ban()

        else:
            embed = Embed(member)
            embed = await embed.member_leave()

        if sanction_kick:

            cursor.execute("""
            SELECT Logs.member_kick
            FROM Logs
            INNER JOIN Guild
            ON Logs.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))
        elif sanction_ban:

            cursor.execute("""
            SELECT Logs.member_ban
            FROM Logs
            INNER JOIN Guild
            ON Logs.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))
        else:
            cursor.execute("""
            SELECT Logs.member_leave
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
            log_channel_id = False if not log_channel_id else log_channel_id[0][0]
            if not log_channel_id:
                close_connexion(connexion)
                return
        else:
            close_connexion(connexion)
            return

        channel_send = self.client.get_channel(log_channel_id)
        await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventGuildMemberLeave(client))
