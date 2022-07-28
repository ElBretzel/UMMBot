import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import sqlite3
import pytz

from constants import Role, Guild_Info, BOT_ID

from rules.badwordsMessage import CheckBadWords
from rules.linkMessage import DetectLink

from embed.logs.EmbedMUpdate import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventMemberUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def search_update(self, dict_before, dict_after):
        for k in dict_before.keys():
            if len(dict_before[k]) > len(dict_after[k]):  # delete
                return [(k, "d", v) for v in dict_before[k] if v not in dict_after[k]]
            elif len(dict_after[k]) > len(dict_before[k]):  # add
                return [(k, "a", v) for v in dict_after[k] if v not in dict_before[k]]
            elif dict_after[k] != dict_before[k]:  # edit
                return [(k, "e", dict_after[k])]

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        member = before
        if member.bot:
            return

        guild = member.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Logs.member_update
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
        else:
            log_channel_id = False

        before_role = [Role(br).id_ for br in before.roles]

        after_role = [Role(ar).id_ for ar in after.roles]

        if before.activities != after.activities:
            close_connexion(connexion)
            return

        dict_before = {"role": before_role, "nick": (before.nick,)}
        dict_after = {"role": after_role, "nick": (after.nick,)}

        if dict_before == dict_after:
            close_connexion(connexion)
            return

        result = await self.search_update(dict_before, dict_after)
        result = result[0]

        moderator = None

        if result[0] == 'nick':
            content = after.display_name
            type_ = "u"

            async for entry in guild.audit_logs(limit=1,
                                                action=discord.AuditLogAction.member_update).filter(
                lambda m: m.target.id == member.id and m.user.id != member.id):

                if entry.user.bot:
                    return

                tz = pytz.timezone('Europe/Paris')
                current_time = datetime.now(tz)
                entry_creation = entry.created_at.replace(tzinfo=pytz.utc).astimezone(tz)

                if current_time - timedelta(seconds=3) <= entry_creation <= current_time + timedelta(
                        seconds=3):
                    moderator = entry.user

            if moderator:
                embed = Embed(member, content, mod=moderator).mod_update_nick()

            else:
                embed = Embed(member, content).member_update_nick()

        elif result[0] == 'role':

            cursor.execute("""
            SELECT Role.id
            FROM Role
            WHERE Role.guild_id = ? AND Role.tmute = 1
            """, (guild.id,))
            tmute_id = cursor.fetchone()

            if tmute_id:
                tmute_id = tmute_id[0]

            if tmute_id == result[2]:
                return

            content = type_ = ""

            async for entry in guild.audit_logs(limit=1,
                                                action=discord.AuditLogAction.member_role_update).filter(
                lambda m: m.target.id == member.id and m.user.id != member.id):

                if entry.user.bot:
                    return

                tz = pytz.timezone('Europe/Paris')
                current_time = datetime.now(tz)
                entry_creation = entry.created_at.replace(tzinfo=pytz.utc).astimezone(tz)

                if current_time - timedelta(seconds=3) <= entry_creation <= current_time + timedelta(
                        seconds=3):
                    moderator = entry.user

            if moderator:
                embed = Embed(member, result[2], result[1], mod=moderator).mod_update_role()
            else:
                embed = Embed(member, result[2], result[1]).member_update_role()
        if moderator:

            roles = Role(member.roles)

            role_perms = roles.permissions_ if hasattr(roles, 'role') else []

            for role in role_perms:
                if role["manage_guild"] or role['administrator'] or role['manage_nicknames'] or \
                        role['manage_roles']:
                    close_connexion(connexion)
                    return
        else:

            if member.id != guild.owner.id:

                tasks = [CheckBadWords, DetectLink]
                tasks = tuple(t(self.client, content, guild) for t in tasks)
                func = [tasks[0].spellcheck, tasks[1].message_link]

                results = await asyncio.gather(*func)

                for index, res in enumerate(results):
                    if res:
                        await tasks[index].rule_break(member, None, log_channel_id, res, type_)
                        close_connexion(connexion)
                        return

        if embed and log_channel_id:

            if moderator and moderator.bot:
                connexion.commit()
                return

            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventMemberUpdate(client))
