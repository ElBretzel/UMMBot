import re
import sqlite3

from embed.rules.embedSpoiler import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleSpoilerMessage:
    def __init__(self, client, message, *args):
        self.client = client
        self.message = message

    async def warn_process(self, member, channel, cursor, connexion):
        cursor.execute("""
        INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
        VALUES ( ?, ?, ?, ?, ? )
        ;     
        """, (member.guild.id, self.client.user.id, member.id, "DELETE", "BOT"))
        connexion.commit()

        await self.message.delete()
        await channel.send(content=f"""<@{member.id}>
```diff
- Il est interdit d'utiliser les spoilers dans vos messages.
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def message_spoiler(self):

        re_match = re.findall(r"\|\|[-a-zA-Z0-9()@:%_\+.~#?`|&/=,! ]*\|\|", self.message.content)
        if not re_match:
            return

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

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

        return [i.replace("||", '') for i in re_match]

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.spoil_message
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RSpoil_Message.timemute, RSpoil_Message.nbefore_mute
        FROM RSpoil_Message
        INNER JOIN Guild
        ON RSpoil_Message.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = 'Utilisation de spoiler'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RSPOIL', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result, sanction_id)
            embed = await embed.spoil_message()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RSPOIL", check_pun)

        close_connexion(connexion)
