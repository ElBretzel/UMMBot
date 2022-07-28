import sqlite3

from embed.rules.embedCaps import Embed

from utils.sql.create_sanction import sanction_process
from utils.sql.rules_automod import automod_mute_sanction


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleCapsMessage:
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
- Nous avons détecté dans votre dernier message un nombre important de caractères en majuscules. 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def message_caps(self):

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RCaps_Message.activate, RCaps_Message.limite
        FROM RCaps_Message
        INNER JOIN Guild
        ON RCaps_Message.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        global_authorization, limit = cursor.fetchall()[0]

        cursor.execute("""
        SELECT Text_Channel.caps_message
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

        message_str = [m for m in self.message.content if m.isalpha()]
        if len(message_str) <= limit:
            return

        ind_upper = 0
        for msg in message_str:
            if msg.isupper():
                ind_upper += 1

        percentage = (ind_upper * 100) / len(message_str)
        if percentage >= 75:
            return percentage

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.caps_message
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RCaps_Message.timemute, RCaps_Message.nbefore_mute
        FROM RCaps_Message
        INNER JOIN Guild
        ON RCaps_Message.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = 'Trop de majuscules'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RCAPS', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, round(result, 1), sanction_id)
            embed = await embed.caps_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RCAPS", check_pun)

        close_connexion(connexion)
