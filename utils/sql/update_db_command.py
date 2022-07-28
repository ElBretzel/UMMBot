import sqlite3
import discord

from utils.sql.get_log import get_logs_moderation
from constants import CHANNEL_LOG
from utils.error_handler import ErrorUnknownAliase, ErrorDontExist, ErrorAlreadyExist

ALIASES = {"allow": ["add", "allow", 1, "True", "a"],
           "deny": ["remove," "deny", 0, "False", "d", "r"]}


class EditDBPerms:

    def __init__(self):
        self.connexion = sqlite3.connect("database.db")
        self.cursor = self.connexion.cursor()

    def commit_and_close(self):
        self.connexion.commit()
        self.connexion.close()

    @property
    def get_value(self):
        return self.cursor.fetchall()

    async def set_automod_perms(self, access, rule, ctx):

        self.cursor.execute(f"""
        SELECT Automoderation.{rule}
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        automod_authorization = self.get_value[0][0]

        if access in ALIASES["allow"]:
            if not automod_authorization:
                self.cursor.execute(f"""
                UPDATE Automoderation
                SET {rule} = 1
                WHERE Automoderation.id = ?
                """, (ctx.guild.id,))
                self.commit_and_close()
                return f"L'automodérateur **obéira** désormais au module '{rule}'"
            else:
                raise ErrorAlreadyExist

        elif access in ALIASES["deny"]:
            if automod_authorization:
                self.cursor.execute(f"""
                UPDATE Automoderation
                SET {rule} = 0
                WHERE Automoderation.id = ?
                """, (ctx.guild.id,))
                self.commit_and_close()
                return f"L'automodérateur **n'obéira plus** au module '{rule}'"
            else:
                raise ErrorDontExist

        else:
            raise ErrorUnknownAliase

    async def set_channel_perms(self, access, rule, ctx, channel_id):

        self.cursor.execute(f"""
        SELECT Text_Channel.{rule}
        FROM Text_Channel
        INNER JOIN Channel
        ON Text_Channel.id = Channel.id
        INNER JOIN Guild
        ON Channel.guild_id = Guild.id
        WHERE Guild.id = ? AND Text_Channel.id = ?
        """, (ctx.guild.id, channel_id))

        channel_authorization = self.get_value[0][0]

        if access in ALIASES["allow"]:
            if not channel_authorization:
                self.cursor.execute(f"""
                UPDATE Text_Channel
                SET {rule} = 1
                WHERE Text_Channel.id = ?
                """, (channel_id,))
                self.commit_and_close()
                return f"Le salon <#{channel_id}> **obéira** désormais à la règle '{rule}' de l'automodération"
            else:
                return f"Le salon <#{channel_id}> **obéis déjà** à la règle '{rule}' de l'automodération"

        elif access in ALIASES["deny"]:
            if channel_authorization:
                self.cursor.execute(f"""
                UPDATE Text_Channel
                SET {rule} = 0
                WHERE Text_Channel.id = ?
                """, (channel_id,))
                self.commit_and_close()
                return f"Le salon <#{channel_id}> **n'obéira plus** à la règle '{rule}' de l'automodération"
            else:
                return f"Le salon <#{channel_id}> **n'obéis déjà pas** à la règle '{rule}' de l'automodération"

        else:
            raise ErrorUnknownAliase

    async def set_logs_perms(self, access, log_type, ctx):

        self.cursor.execute(f"""
        SELECT Logs.{log_type}
        FROM Logs
        INNER JOIN Guild
        ON Logs.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        logs_authorization = self.get_value[0][0]

        if access in ALIASES["allow"]:
            if not logs_authorization:
                self.cursor.execute(f"""
                UPDATE Logs
                SET {log_type} = 1
                WHERE Logs.id = ?
                """, (ctx.guild.id,))
                self.commit_and_close()
                return f"Les salons logs **afficheront désormais** le module '{log_type}'"
            else:
                raise ErrorAlreadyExist

        elif access in ALIASES["deny"]:
            if logs_authorization:
                self.cursor.execute(f"""
                UPDATE Logs
                SET {log_type} = 0
                WHERE Logs.id = ?
                """, (ctx.guild.id,))
                self.commit_and_close()
                return f"Les salons logs **n'afficheront plus** le module '{log_type}'"
            else:
                raise ErrorDontExist

        else:
            raise ErrorUnknownAliase

    async def set_logs_channel(self, access, log_type, channel, ctx):

        if log_type in ["message", "msg", "texte", "txt", "logs_message"]:
            log_types = "logs_message"
        elif log_type in ["voice", "vocal", "voc", "logs_voice"]:
            log_types = "logs_voice"
        elif log_type in ["moderation", "admin", "mod", "logs_admin"]:
            log_types = "logs_admin"
        elif log_type in ["sanction", "punition", "pun", "logs_sanction"]:
            log_types = "logs_sanction"
        else:
            raise ErrorUnknownAliase

        channel_id = await get_logs_moderation(channel.guild, log_types)

        if not channel_id and not access:
            raise ErrorDontExist

        if access:
            self.cursor.execute(f"""
            UPDATE Channel
            SET {log_types} = 1
            WHERE id = ? AND guild_id = ? 
            """, (channel.id, channel.guild.id))
            self.connexion.commit()

        if not access or channel_id:
            self.cursor.execute(f"""
            UPDATE Channel
            SET {log_types} = 0
            WHERE id = ? AND guild_id = ? 
            """, (channel.id, channel.guild.id))
            self.connexion.commit()

        self.commit_and_close()
        dict_ = {}
        if channel_id:
            dict_["old"] = channel_id
            dict_["old_text"] = f"Le salon **<#{channel_id.id}>** vient d'être **désassigné** des {CHANNEL_LOG[log_types].lower()}"
        if access:
            dict_["new_text"] = f"Le salon **<#{channel.id}>** est désormais **assigné** aux {CHANNEL_LOG[log_types].lower()}"
        return dict_

    async def set_mod_role(self, ctx, role, access):

        role_id = role.id

        self.cursor.execute("""
        SELECT Role.id
        FROM Role
        INNER JOIN Guild
        ON Role.guild_id = Guild.id
        WHERE Guild.id = ? AND Role.moderation = 1
        """, (ctx.guild.id,))

        roles = self.get_value

        if roles:
            roles = [i[0] for i in roles]

        for ro in roles:
            if ro == role_id:
                if access in ALIASES["allow"]:
                    self.commit_and_close()
                    return f"Le rôle **<@&{role_id}>** fait **déjà parti** de la modération"
                elif access in ALIASES["deny"]:
                    self.cursor.execute("""
                    UPDATE Role
                    SET moderation = 0
                    WHERE guild_id = ? AND id = ?
                    """, (ctx.guild.id, role_id))
                    self.commit_and_close()
                    return f"Le rôle **<@&{role_id}>** ne fait **désormais plus parti** de la modération"
                else:
                    raise ErrorUnknownAliase
        else:
            if access in ALIASES["allow"]:
                self.cursor.execute("""
                UPDATE Role
                SET moderation = 1
                WHERE guild_id = ? AND id = ?
                """, (ctx.guild.id, role_id))
                self.commit_and_close()
                return f"Le rôle **<@&{role_id}>** fait **désormais parti** de la modération"
            elif access in ALIASES["deny"]:
                return f"Le rôle **<@&{role_id}>** ne fait **pas parti** de la modération"
            else:
                raise ErrorUnknownAliase

    async def set_member_mention(self, ctx, member, access):

        member_id = member.id

        self.cursor.execute("""
        SELECT Member.is_blocked
        FROM Member
        INNER JOIN Guild
        ON Member.guild_id = Guild.id
        WHERE Guild.id = ? AND Member.member_id = ?
        ;
        """, (ctx.guild.id, member_id))

        block = self.get_value[0][0]

        if access in ALIASES["allow"]:
            if block:
                self.commit_and_close()
                return f"L'utilisateur **<@{member.id}>** est **déjà bloqué** du système de mention"
            else:
                self.cursor.execute("""
                UPDATE Member
                SET is_blocked = 1
                WHERE Member.guild_id = ? AND Member.member_id = ?
                ;
                """, (ctx.guild.id, member_id))
                self.commit_and_close()
                return f"L'utilisateur **<@{member.id}>** **vient d'être bloqué** du système de mention"

        elif access in ALIASES["deny"]:
            if not block:
                self.commit_and_close()
                return f"L'utilisateur **<@{member.id}>** est **déjà débloqué** du système de mention"
            self.cursor.execute("""
                UPDATE Member
                SET is_blocked = 0
                WHERE Member.guild_id = ? AND Member.member_id = ?
                ;
                """, (ctx.guild.id, member_id))
            self.commit_and_close()
            return f"L'utilisateur **<@{member.id}>** **vient d'être débloqué** du système de mention"

        else:
            raise ErrorUnknownAliase

    async def add_badword(self, ctx, word):

        self.cursor.execute("""
        SELECT Custom_Badwords.word
        FROM Custom_Badwords
        INNER JOIN Guild
        ON Custom_Badwords.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        badwords = self.get_value

        if badwords:
            badwords = [i[0] for i in badwords]

            for bw in badwords:
                if bw == word:
                    self.commit_and_close()
                    raise ErrorAlreadyExist
        self.cursor.execute("""
        INSERT INTO Custom_Badwords ( id, word )
        VALUES ( ?, ? )
        """, (ctx.guild.id, word))
        self.commit_and_close()
        return f"**{word.capitalize()}** est désormais un mot interdit sur le serveur"

    async def delete_badword(self, ctx, word):

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
            raise ErrorDontExist

        badwords = [i[0] for i in badwords]
        for bw in badwords:
            if bw == word:
                self.cursor.execute("""
                DELETE FROM Custom_Badwords
                WHERE Custom_Badwords.id = ? AND Custom_Badwords.word = ?
                """, (ctx.guild.id, word))
                self.commit_and_close()
                return f"**{word.capitalize()}** est désormais un mot autorisé sur le serveur"
        else:
            self.commit_and_close()
            raise ValueError

    async def add_link(self, ctx, link, access):

        self.cursor.execute("""
        SELECT Link_Info.word
        FROM Link_Info
        INNER JOIN Guild
        ON Link_Info.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        links = self.get_value

        if links:
            links = [i[0] for i in links]

            for li in links:
                if li == link:
                    self.commit_and_close()
                    raise ErrorAlreadyExist

        self.cursor.execute("""
        INSERT INTO Link_Info ( id, word, state )
        VALUES ( ?, ?, ? )
        """, (ctx.guild.id, link, access))
        self.commit_and_close()

        if access:
            return f"Le lien '**{link}**' a été whitelist avec succès"
        else:
            return f"Le lien '**{link}**' a été blacklist avec succès"

    async def delete_link(self, ctx, link):

        self.cursor.execute("""
        SELECT Link_Info.word
        FROM Link_Info
        INNER JOIN Guild
        ON Link_Info.id = Guild.id
        WHERE Guild.id = ?
        """, (ctx.guild.id,))

        links = self.get_value

        if not links:
            self.commit_and_close()
            raise ErrorDontExist

        links = [i[0] for i in links]
        for li in links:
            if li == link:
                self.cursor.execute("""
                DELETE FROM Link_Info
                WHERE Link_Info.id = ? AND Link_Info.word = ?
                """, (ctx.guild.id, link))
                self.commit_and_close()
                return f"Le lien '**{link}**' a été de nouveau autorisé avec succès"
        else:
            self.commit_and_close()
            raise ErrorDontExist

    async def clear_sanctions(self, ctx, user, type_):

        self.cursor.execute("""
        DELETE FROM Sanction
        WHERE Sanction.guild_id = ? AND Sanction.sanction_user_id = ? AND Sanction.sanction_type = ?
        """, (ctx.guild.id, user.id, type_))

        self.commit_and_close()

    async def clear_sanction(self, sanction_id):
        self.cursor.execute("""
        DELETE FROM Sanction
        WHERE Sanction.id = ?
        """, (sanction_id,))

        self.commit_and_close()

    async def update_rule_settings(self, rule, rule_setting):
        print(rule, rule_setting)
        self.cursor.execute(f"""
        UPDATE {rule}
        SET {','.join([f'{i}={j}' for i, j in rule_setting.items()])}
        """)

        self.commit_and_close()
