import re
import sqlite3

from embed.rules.embedBMention import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleBlockMention:
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
- Nous avons détecté dans votre dernier message une mention vers un membre ou un groupe interdit à mentionner. 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)


    @property
    async def block_mention(self):

        default_mention = re.findall(r"(?:@everyone)|(?:@here)", self.message.content)
        if not (self.message.mentions or default_mention):
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        channel = self.message.channel
        guild = self.message.guild

        cursor.execute("""
        SELECT RBlock_Mention.activate
        FROM RBlock_Mention
        INNER JOIN Guild
        ON RBlock_Mention.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        global_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT Text_Channel.block_mention
        FROM Text_Channel
        INNER JOIN Channel
        ON Text_Channel.id = Channel.id
        WHERE Channel.id = ?
        ;    
        """, (channel.id,))
        channel_authorization = cursor.fetchall()[0][0]

        if not channel_authorization or not global_authorization:
            close_connexion(connexion)
            return

        if default_mention:
            list_ = [d for d in default_mention]
            list_.append("e")
            close_connexion(connexion)
            return list_

        cursor.execute("""
        SELECT Member.member_id
        FROM Member
        INNER JOIN Guild
        ON Member.guild_id = Guild.id
        WHERE Guild.id = ? AND Member.is_blocked = 1
        ;
        """, (guild.id,))

        list_ = []
        block_user_id = cursor.fetchall()
        block_user_id = [] if not block_user_id else block_user_id[0]
        for mention in self.message.mentions:
            list_ = [str(self.client.get_user(i)) for i in block_user_id if i == mention.id]

        close_connexion(connexion)

        if list_:
            list_.append("u")
            return list_

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
             SELECT RBlock_Mention.timemute, RBlock_Mention.nbefore_mute
             FROM RBlock_Mention
             INNER JOIN Guild
             ON RBlock_Mention.id = Guild.id
             WHERE Guild.id = ?
             ;
             """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        cursor.execute("""
             SELECT Automoderation.block_mention
             FROM Automoderation
             INNER JOIN Guild
             ON Automoderation.id = Guild.id
             WHERE Guild.id = ?
             ;
             """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = 'Mention interdite' if result[-1] == "u" else 'Mention de masse'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RBMENTION', 0)

        if log_channel_id:
            message_detection = ', '.join(result[:-1])
            embed = Embed(member, channel, self.message, message_detection, result[-1], sanction_id)
            embed = await embed.bmention_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RBMENTION", check_pun)

        close_connexion(connexion)
