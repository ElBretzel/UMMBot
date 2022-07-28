from discord.ext import commands
import sqlite3
import asyncio

from constants import Role, Guild_Info

from rules.badwordsMessage import CheckBadWords
from rules.linkMessage import DetectLink

from embed.logs.embedUUpdate import Embed


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventUserUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_user_update(self, before, after):

        user = before
        if user.bot:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Guild.id
        FROM Guild
        INNER JOIN Member
        ON Guild.id = Member.guild_id
        INNER JOIN User
        ON Member.member_id = User.id
        WHERE User.id = ?
        ;
        """, (user.id,))

        guilds = cursor.fetchall()[0]
        guilds = [self.client.get_guild(g) for g in guilds]

        if not guilds:
            close_connexion(connexion)
            return

        members = [g.get_member(user.id) for g in guilds]

        for guild, member in zip(guilds, members):

            guild = member.guild
            if guild.id not in Guild_Info.umm_whitelist:
                close_connexion(connexion)
                return

            cursor.execute("""
            SELECT Logs.user_update
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

            if before.name != after.name:

                roles = Role(member.roles)

                role_perms = roles.permissions_ if hasattr(roles, 'role') else []

                for role in role_perms:
                    if role["manage_guild"] or role['administrator'] or role['manage_nicknames'] or \
                            role['manage_roles']:
                        close_connexion(connexion)
                        break
                else:
                    if member.id != guild.owner.id:

                        tasks = [CheckBadWords, DetectLink]
                        tasks = tuple(t(self.client, after.name, guild) for t in tasks)
                        func = [tasks[0].spellcheck, tasks[1].message_link]

                        results = await asyncio.gather(*func)

                        for index, result in enumerate(results):
                            if result:
                                await tasks[index].rule_break(member, None, log_channel_id, result, "u")
                                break

            elif before.avatar_url != after.avatar_url and log_channel_id:
                embed = Embed(member, before, after)
                embed = await embed.avatar_update()
                channel_send = self.client.get_channel(log_channel_id)
                await channel_send.send(embed=embed)
        close_connexion(connexion)


def setup(client):
    client.add_cog(EventUserUpdate(client))
