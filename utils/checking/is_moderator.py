import sqlite3
from discord.ext import commands
from utils.error_handler import ErrorMemberNotModerator


def check_if_moderator():
    def predicate(ctx):
        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        if ctx.author.id == ctx.guild.owner.id:
            return True

        cursor.execute("""
        SELECT Role.id
        FROM Role
        INNER JOIN Guild
        ON Role.guild_id = Guild.id
        WHERE Guild.id = ? AND Role.moderation = 1
        ;
        """, (ctx.guild.id,))
        result = cursor.fetchall()
        connexion.close()
        if not result:
            raise ErrorMemberNotModerator

        roles = [i[0] for i in result]

        for role in ctx.author.roles:
            if role.id in roles:
                return True
        else:
            raise ErrorMemberNotModerator

    return commands.check(predicate)
