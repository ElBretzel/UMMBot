from datetime import timedelta
import sqlite3
import pytz
import emoji

from embed.rules.embedSMention import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleSpamMention:
    def __init__(self, client, message, *args):
        self.client = client
        self.message = message

    async def warn_process(self, member, channel, cursor, connexion, distance):
        cursor.execute("""
        INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
        VALUES ( ?, ?, ?, ?, ? )
        ;     
        """, (member.guild.id, self.client.user.id, member.id, "DELETE", "BOT"))
        connexion.commit()

        await channel.purge(limit=distance+1, check=lambda m: m.author.id == member.id)
        await channel.send(content=f"""<@{member.id}>
```diff
- Nous avons détecté un interval d'envoi de messages (mention) trop court. Ralentissez votre rythme pour éviter de futur avertissements.
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def spam_mentions(self):

        if not self.message.mentions:
            return

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
         SELECT RSpam_Mention.activate, RSpam_Mention.distance, RSpam_Mention.interval
         FROM RSpam_Mention
         INNER JOIN Guild
         ON RSpam_Mention.id = Guild.id
         WHERE Guild.id = ?
         ;
         """, (guild.id,))
        global_authorization, distance, interval = cursor.fetchall()[0]

        cursor.execute("""
         SELECT Text_Channel.spam_mention
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

        time_list, msg_list = [], []
        tz = pytz.timezone('Europe/Paris')
        async for msg in self.message.channel.history(limit=distance+1).filter(lambda m:
                                                                            m.author.id == self.message.author.id):
            time_list.append(msg.created_at.astimezone(tz))
            msg_list.append(msg)

        mentions = [n for n, men in enumerate(msg_list) if men.mentions]
        send_time = timedelta(seconds=0)

        if len(mentions) > distance:
            for x in range(distance):
                send_time += time_list[mentions[x]] - time_list[mentions[x + 1]]
            if send_time.seconds < interval:
                return [send_time, distance]

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
             SELECT Automoderation.spam_mention
             FROM Automoderation
             INNER JOIN Guild
             ON Automoderation.id = Guild.id
             WHERE Guild.id = ?
             ;
             """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RSpam_Mention.timemute, RSpam_Mention.nbefore_mute, RSpam_Mention.distance
        FROM RSpam_Mention
        INNER JOIN Guild
        ON RSpam_Mention.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion, check_pun[2])
            reason = 'Spam mention'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RSMENTION', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result[0], result[1], sanction_id)
            embed = await embed.smention_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RSMENTION", check_pun)

        close_connexion(connexion)
