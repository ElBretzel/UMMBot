import sqlite3

from embed.rules.embedMMention import Embed

from utils.sql.create_sanction import sanction_process
from utils.sql.rules_automod import automod_mute_sanction


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleMassMention:
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
- Nous avons détecté dans votre dernier message un nombre de mention élevé. 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def mass_mention(self):

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RMass_Mention.activate, RMass_Mention.limite
        FROM RMass_Mention
        INNER JOIN Guild
        ON RMass_Mention.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        global_authorization, limit = cursor.fetchall()[0]

        cursor.execute("""
        SELECT Text_Channel.mass_mention
        FROM Text_Channel
        INNER JOIN Channel
        ON Text_Channel.id = Channel.id
        WHERE Channel.id = ?
        ;    
        """, (channel.id,))
        channel_authorization = cursor.fetchall()[0][0]

        close_connexion(connexion)

        if not channel_authorization or not global_authorization:
            return

        len_mention = len(self.message.mentions)

        if len_mention > limit:
            return len_mention

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
         SELECT Automoderation.mass_mention
         FROM Automoderation
         INNER JOIN Guild
         ON Automoderation.id = Guild.id
         WHERE Guild.id = ?
         ;
         """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
         SELECT RMass_Mention.timemute, RMass_Mention.nbefore_mute
         FROM RMass_Mention
         INNER JOIN Guild
         ON RMass_Mention.id = Guild.id
         WHERE Guild.id = ?
         ;
         """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = 'Mention de masse'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RMMENTION', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result, sanction_id)
            embed = await embed.mmention_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RMMENTION", check_pun)

        close_connexion(connexion)
