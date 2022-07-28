import sqlite3
import discord

from constants import RULES, LOGS

from utils.sql.get_log import get_logs_moderation


class GetDBInfo:

    def __init__(self):
        self.connexion = sqlite3.connect("database.db")
        self.cursor = self.connexion.cursor()

    def commit_and_close(self):
        self.connexion.commit()
        self.connexion.close()

    @property
    def get_value(self):
        return self.cursor.fetchall()

    async def info_automoderation(self, ctx):

        self.cursor.execute(f"""
        SELECT {','.join([f"{i}" for i in RULES])}
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        result = self.get_value[0]
        self.commit_and_close()
        return result

    async def  info_logchannel(self, ctx):
        channels = []

        result = await get_logs_moderation(ctx.guild, "logs_message")

        if result:
            channels += [(result, "salon log message")]
        else:
            channels += [(None, "salon log message")]

        result = await get_logs_moderation(ctx.guild, "logs_voice")

        if result:
            channels += [(result, "salon log vocal")]
        else:
            channels += [(None, "salon log vocal")]

        result = await get_logs_moderation(ctx.guild, "logs_admin")

        if result:
            channels += [(result, "salon log moderation")]
        else:
            channels += [(None, "salon log moderation")]

        result = await get_logs_moderation(ctx.guild, "logs_sanction")

        if result:
            channels += [(result, "salon log sanction")]
        else:
            channels += [(None, "salon log sanction")]

        self.commit_and_close()
        if not channels:
            return

        channels = [(discord.utils.get(ctx.guild.text_channels, id=g.id).id, l) if g else ("Non assigné",l) for g, l in channels]
        return channels

    async def info_logs(self, ctx):

        self.cursor.execute(f"""
        SELECT {','.join([f"{i}" for i in LOGS])}
        FROM Logs
        INNER JOIN Guild
        ON Logs.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))
        infos = self.get_value[0]
        self.commit_and_close()

        return infos

    async def info_badword(self, ctx):

        self.cursor.execute("""
        SELECT Custom_Badwords.word
        FROM Custom_Badwords
        INNER JOIN Guild
        ON Custom_Badwords.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        badwords = self.get_value
        if not badwords:
            self.commit_and_close()
            return ["Vous n'avez paramétré aucun mot interdit..."]

        badwords = [i[0] for i in badwords]
        self.commit_and_close()
        return badwords

    async def info_links(self, ctx):

        self.cursor.execute("""
        SELECT Link_Info.word, Link_Info.state
        FROM Link_Info
        INNER JOIN Guild
        ON Link_Info.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        links = self.get_value
        if not links:
            self.commit_and_close()
            return [("Vous n'avez paramétré aucun lien...", False)]

        links = [(i[0], i[1]) for i in links]
        self.commit_and_close()
        return links

    async def info_blocked_user(self, ctx):

        self.cursor.execute("""
        SELECT Member.member_id
        FROM Member
        INNER JOIN Guild
        ON Member.guild_id = Guild.id
        WHERE Guild.id = ? AND Member.is_blocked = 1
        """, (ctx.guild.id,))

        members = self.get_value
        if not members:
            self.commit_and_close()
            return

        self.commit_and_close()

        members = [i[0] for i in members]
        members = [discord.utils.get(ctx.guild.members, id=m).id for m in members]
        return members

    async def info_moderation(self, ctx):

        self.cursor.execute("""
        SELECT Role.id
        FROM Role
        INNER JOIN Guild
        ON Role.guild_id = Guild.id
        WHERE Guild.id = ? AND Role.moderation = 1
        """, (ctx.guild.id,))

        roles = self.cursor.fetchall()
        if not roles:
            self.commit_and_close()
            return

        self.commit_and_close()

        roles = [i[0] for i in roles]
        roles = [discord.utils.get(ctx.guild.roles, id=r).id for r in roles]
        return roles

    async def info_channel(self, ctx, channel):

        self.cursor.execute(f"""
        SELECT {','.join([f"{i}" for i in RULES])}
        FROM Text_Channel
        INNER JOIN Channel
        ON Text_Channel.id = Channel.id
        INNER JOIN Guild
        ON Channel.guild_id = Guild.id
        WHERE Guild.id = ? AND Channel.id = ?
        """, (ctx.guild.id, channel.id))

        result = self.get_value[0]
        self.commit_and_close()

        return result

    async def info_sanctions(self, ctx, user):
        self.cursor.execute("""
        SELECT sanction_type, sanction_description, sanction_mod_id, sanction_user_id, sanction_create, punished, Sanction.id, guild_id
        FROM Sanction
        INNER JOIN Guild
        ON Guild.id = Sanction.guild_id
        WHERE Guild.id = ? and Sanction.sanction_user_id = ?
        ORDER BY sanction_create ASC
        ;""", (ctx.guild.id, user.id))

        result = self.get_value
        self.commit_and_close()

        warn = []
        kick = []
        mute = []
        ban = []
        for i in result:
            if i[0] == "WARN":
                warn.append([j for j in i])
            elif i[0] == "KICK":
                kick.append([j for j in i])
            elif i[0] == "BAN":
                ban.append([j for j in i])
            else:
                mute.append([j for j in i])

        return {"WARN": (len(warn), warn),
                "KICK": (len(kick), kick),
                "MUTE": (len(mute), mute),
                "BAN": (len(ban), ban)}

    async def info_sanction(self, sanction_id):
        self.cursor.execute("""
        SELECT sanction_type, sanction_description, sanction_mod_id, sanction_user_id, sanction_create, punished, Sanction.id, guild_id, sanction_finish
        FROM Sanction
        WHERE Sanction.id = ?
        ORDER BY sanction_create ASC
        ;""", (sanction_id,))
        result = self.get_value[0]
        self.commit_and_close()

        return result


