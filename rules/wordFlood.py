import sqlite3

from embed.rules.embedFWord import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleWordFlood:
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
- Nous avons détecté dans votre dernier message un nombre important de mots identiques.
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def flood_word(self):

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RFlood_Word.activate, RFlood_Word.limite, RFlood_Word.distance
        FROM RFlood_Word
        INNER JOIN Guild
        ON RFlood_Word.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        global_authorization, limit, distance = cursor.fetchall()[0]
        distance += 2

        cursor.execute("""
        SELECT Text_Channel.flood_word
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

        split_message = [m.split(" ") for m in self.message.content.splitlines()]

        for cols in split_message:
            for n, rows in enumerate(cols):

                len_check = len(cols) - n if len(cols) - n < (distance * limit) + 1 else (
                                                              distance * limit) + 1
                if len_check < limit:
                    return
                if not rows.isalpha():
                    break

                error = done = 0
                for loop in range(len_check):
                    if rows != cols[n + loop]:
                        error += 1

                    elif loop != 0:
                        error = 0
                        done += 1

                    if loop != 0 and done >= limit:
                        return rows

                    elif error == distance + 1:
                        break

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.flood_word
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RFlood_Word.timemute, RFlood_Word.nbefore_mute
        FROM RFlood_Word
        INNER JOIN Guild
        ON RFlood_Word.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = 'Flood de mot'
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RFWORD', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result, sanction_id)
            embed = await embed.fword_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RFWORD", check_pun)

        close_connexion(connexion)
