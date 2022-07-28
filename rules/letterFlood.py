import sqlite3

from embed.rules.embedFLetter import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleLetterFlood:
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
- Nous avons détecté dans votre dernier message un nombre important de lettres identiques. 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir recu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def flood_letter(self):

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RFlood_Letter.activate, RFlood_Letter.limite
        FROM RFlood_Letter
        INNER JOIN Guild
        ON RFlood_Letter.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        global_authorization, limit = cursor.fetchall()[0]

        cursor.execute("""
        SELECT Text_Channel.flood_letter
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

        split_message = [m.lower().split(" ") for m in self.message.content.splitlines()]
        for line in split_message:
            for word in line:
                for n_l, letter in enumerate(word):
                    if len(word) - n_l < limit or word.count(letter) <= limit:
                        continue
                    else:
                        ind_lflood = 0
                        for i in range(limit):
                            if letter not in word[i:i + 2]:
                                break
                            else:
                                ind_lflood += 1
                            if ind_lflood == limit - 1:
                                return letter

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.flood_letter
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RFlood_Letter.timemute, RFlood_Letter.nbefore_mute
        FROM RFlood_Letter
        INNER JOIN Guild
        ON RFlood_Letter.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = "Flood de lettre"
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RFLETTER', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result, sanction_id)
            embed = await embed.fletter_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RFLETTER", check_pun)

        close_connexion(connexion)
