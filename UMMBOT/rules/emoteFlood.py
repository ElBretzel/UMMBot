import emoji
import sqlite3
import re

from embed.rules.embedFEmote import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class RuleEmoteFlood:
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
- Nous avons détecté dans votre dernier message un nombre d'emotes par ligne trop élevée. 
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

    @property
    async def flood_emotes(self):

        channel = self.message.channel
        guild = self.message.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RFlood_Emote.activate, RFlood_Emote.limite
        FROM RFlood_Emote
        INNER JOIN Guild
        ON RFlood_Emote.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        global_authorization, check_emotes = cursor.fetchall()[0]

        cursor.execute("""
        SELECT Text_Channel.flood_emote
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

        gcounter = 0

        message_content = [m.split(" ") for m in self.message.content.splitlines()]
        for line in message_content:
            emotes = 0
            for word in line:
                emotes += emoji.emoji_count(word)
                emotes += len(re.findall(r"<:\w{1,100}:\d{1,100}>", word))
                gcounter += emotes
            if emotes > check_emotes or gcounter > 20:
                return emotes

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        guild = channel.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.flood_emote
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RFlood_Emote.timemute, RFlood_Emote.nbefore_mute
        FROM RFlood_Emote
        INNER JOIN Guild
        ON RFlood_Emote.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        if automod_authorization:
            await self.warn_process(member, channel, cursor, connexion)
            reason = "Flood d'emote"
            sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RFEMOTE', 0)

        if log_channel_id:
            embed = Embed(member, channel, self.message, result, sanction_id)
            embed = await embed.femote_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization:
            await automod_mute_sanction(self.client, guild, member, "RFEMOTE", check_pun)

        close_connexion(connexion)
