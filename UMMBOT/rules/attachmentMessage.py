import sqlite3

from constants import Attachment

from embed.rules.embedAttachment import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class AttachMessage:
    def __init__(self, client, message, *args):
        self.client = client
        self.message = message
        self.file = None

    async def warn_process(self, member, channel, result, cursor, connexion):
        cursor.execute("""
        INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
        VALUES ( ?, ?, ?, ?, ? )
        ;     
        """, (channel.guild.id, self.client.user.id, member.id, "DELETE", "BOT"))
        connexion.commit()

        await self.message.delete()
        await channel.send(content=f"""<@{member.id}>
```diff
- Nous avons détecté dans votre dernier message un fichier incorrect ({result}). 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir recu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def msg_attach(self):

        attachment = self.message.attachments

        if not attachment:
            return

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        for a in attachment:
            self.file = Attachment(a)
            ext = self.file.check_extension_
            spoiler = self.file.spoiler_

            if ext:
                cursor.execute("""
                SELECT RAttach_Message.activate
                FROM RAttach_Message
                INNER JOIN Guild
                ON RAttach_Message.id = Guild.id
                WHERE Guild.id = ?
                ;
                """, (guild.id,))

                module_authorization = cursor.fetchall()[0][0]

                cursor.execute("""
                SELECT Text_Channel.msg_attachment
                FROM Text_Channel
                INNER JOIN Channel
                ON Text_Channel.id = Channel.id
                WHERE Channel.id = ?
                ; 
                """, (channel.id,))

                channel_authorization = cursor.fetchall()[0][0]

                close_connexion(connexion)
                if not module_authorization or not channel_authorization:
                    return
                return f"{ext}"

            elif spoiler:

                cursor.execute("""
                SELECT RSpoil_Message.activate
                FROM RSpoil_Message
                INNER JOIN Guild
                ON RSpoil_Message.id = Guild.id
                WHERE Guild.id = ?
                ;
                """, (guild.id,))

                global_authorization = cursor.fetchall()[0][0]

                cursor.execute("""
                SELECT Text_Channel.spoil_message
                FROM Text_Channel
                INNER JOIN Channel
                ON Text_Channel.id = Channel.id
                WHERE Channel.id = ?
                ; 
                """, (channel.id,))

                channel_authorization = cursor.fetchall()[0][0]

                close_connexion(connexion)
                if not global_authorization or not channel_authorization:
                    return

                return "spoiler"

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        guild = channel.guild
        rule_type = 'RSPOIL' if result == "spoiler" else 'RATTACH'

        if result == "spoiler":
            cursor.execute("""
            SELECT RSpoil_Message.timemute, RSpoil_Message.nbefore_mute
            FROM RSpoil_Message
            INNER JOIN Guild
            ON RSpoil_Message.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))

            check_pun = cursor.fetchall()[0]

            cursor.execute("""
            SELECT Automoderation.spoil_message
            FROM Automoderation
            INNER JOIN Guild
            ON Automoderation.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))

        else:
            cursor.execute("""
            SELECT RAttach_Message.timemute, RAttach_Message.nbefore_mute
            FROM RAttach_Message
            INNER JOIN Guild
            ON RAttach_Message.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))

            check_pun = cursor.fetchall()[0]

            cursor.execute("""
            SELECT Automoderation.msg_attachment
            FROM Automoderation
            INNER JOIN Guild
            ON Automoderation.id = Guild.id
            WHERE Guild.id = ?
            ;
            """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, result, cursor, connexion)
            reason = 'Utilisation de spoiler' if result == "spoiler" else 'Nom d extension de fichier dangereux'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, rule_type, 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, self.file, result, sanction_id)
            embed = await embed.attachment_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, rule_type, check_pun)

        close_connexion(connexion)
