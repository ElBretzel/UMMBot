import re
import sqlite3
import pytz
from datetime import datetime

from embed.rules.embedLink import Embed
from embed.logs.embedQuitAndMute import EmbedMute

from utils.action.converter import time_reason
from utils.action.timed_mute import TimeMute

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process

from constants import Infraction


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class DetectLink:
    def __init__(self, client, message, *args):
        self.client = client
        self.message = message
        self.args = args

    async def warn_process(self, member, channel, type_, cursor, connexion, guild):
        if type_ == "m":
            cursor.execute("""
            INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
            VALUES ( ?, ?, ?, ?, ? )
            ;     
            """, (member.guild.id, self.client.user.id, member.id, "DELETE", "BOT"))
            connexion.commit()

            await self.message.delete()
            await channel.send(content=f"""<@{member.id}>
```diff
- Vous ne pouvez pas envoyer de lien externe sur ce salon ou l'administrateur a désactivé l'envoi de ce nom de domaine sur le serveur.
Si vous ne voyez pas pourquoi votre message a été supprimé ou que vous pensez avoir reçu cet avertissement injustement,
rentrez la commande " -new " dans le salon commande.```""", delete_after=15)

        elif type_ == "u":
            await member.edit(nick="? Pseudo")

            tz = pytz.timezone('Europe/Paris')

            date = datetime.now(tz)
            mem_join = member.joined_at
            mem_join = mem_join.astimezone(tz)
            mem_duration = date - mem_join

            if mem_duration.seconds > 3:
                return

            cursor.execute("""
            SELECT sanction_finish, sanction_type, Sanction.id
            FROM Sanction
            INNER JOIN Guild
            ON Guild.id = guild_id
            WHERE Guild.id = ? AND sanction_user_id = ? AND (sanction_type = 'MUTE' OR sanction_type = 'VMUTE' OR sanction_type = 'GMUTE') AND punished = 0
            ORDER BY Sanction.id DESC
            LIMIT 1
            """, (guild.id, member.id))
            sanction_finish = cursor.fetchone()

            if sanction_finish:
                sanction_time = datetime.strptime(sanction_finish[0], "%Y-%m-%d %H:%M:%S").astimezone(tz)
                date = datetime.now(tz)

                if date < sanction_time:
                    return [sanction_time - date, sanction_finish]

    @property
    async def message_link(self):

        if self.args:
            guild = self.args[0]
            message_content = self.message
        else:
            guild = self.message.guild
            channel = self.message.channel
            message_content = self.message.content

        re_match = re.findall(
            r"((?:(https?:\/\/)|(www\.))([-a-zA-Z0-9@:%_\+~#=\.]{1,256}\.[a-zA-Z0-9()]{1,6})([-a-zA-Z0-9("
            r")@:%_\+\.~#?&//=,!]*))", message_content)

        if not re_match:
            return

        re_match.append([])

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RLink_Message.activate
        FROM RLink_Message
        INNER JOIN Guild
        ON RLink_Message.id = Guild.id
        WHERE Guild.id = ?
        """, (guild.id,))

        global_authorization = cursor.fetchall()[0][0]

        if not self.args:
            cursor.execute("""
            SELECT Text_Channel.link_message
            FROM Text_Channel
            INNER JOIN Channel
            ON Text_Channel.id = Channel.id
            WHERE Channel.id = ?
            ; 
            """, (channel.id,))

            channel_authorization = cursor.fetchall()[0][0]
        else:
            channel_authorization = True

        if not global_authorization or not channel_authorization:
            close_connexion(connexion)
            return

        cursor.execute("""
        SELECT Link_info.word, Link_info.state
        FROM Link_info
        INNER JOIN RLink_Message
        ON Link_info.id = RLink_Message.id
        WHERE RLink_Message.id = ?
        ;
        """, (guild.id,))

        link_info = cursor.fetchall()

        close_connexion(connexion)

        whitelist = [i[0] for i in link_info if i[1] == 1]
        blacklist = [i[0] for i in link_info if i[1] == 0]

        for i in blacklist:
            if re_match[0][3] == i:
                re_match[1].append('b')
                return re_match

        for i in whitelist:
            if re_match[0][3] == i:
                return

        if re_match[0][1] != '':
            re_match[1].append('o')
        elif re_match[0][2] != '':
            re_match[1].append('n')

        if re_match[0][3] == 'discord.gg':
            re_match[1].append('d')

        return re_match

    async def rule_break(self, member, channel, log_channel_id, result, *args):

        detection_type = args[0]
        result[1] = ''.join(result[1])

        if "d" in result[1]:
            content = f"**lien discord**: {result[0][4]}"

        elif "o" in result[1]:
            content = f"**lien cliquable** potentiellement dangereux: {result[0][3]}"

        elif "n" in result[1]:
            content = f"**lien non cliquable**: {result[0][3]}"

        else:
            content = f"**lien blacklist**: {result[0][3]}"

        guild = member.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Automoderation.link_message
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]

        cursor.execute("""
        SELECT RLink_Message.timemute, RLink_Message.nbefore_mute
        FROM RLink_Message
        INNER JOIN Guild
        ON RLink_Message.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        sanction_id = None
        join_mute = None
        if automod_authorization:
            join_mute = await self.warn_process(member, channel, detection_type, cursor, connexion, guild)
            reason = 'Lien message' if detection_type == "m" else 'Lien pseudonyme'

            if not join_mute:
                sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id, 'RLINK', 0)

        if log_channel_id and not join_mute:
            embed = Embed(member, channel, self.message, content, detection_type, sanction_id)
            embed = await embed.link_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization and "n" not in result[1] and not join_mute:
            await automod_mute_sanction(self.client, guild, member, "RLINK", check_pun)
            close_connexion(connexion)
            return

        if join_mute:

            cursor.execute("""
            SELECT Channel.id
            FROM Channel
            INNER JOIN Guild
            ON Channel.guild_id = Guild.id
            WHERE Guild.id = ? AND Channel.logs_sanction = 1
            ;
            """, (guild.id,))
            log_channel_id = cursor.fetchall()
            log_channel_id = None if not log_channel_id else log_channel_id[0][0]

            timereason = await time_reason(join_mute[0].total_seconds())
            close_connexion(connexion)

            if join_mute[1][1] == "MUTE":
                embed = await EmbedMute(member, timereason, join_mute[1][2]).member_mute(Infraction.mute.value)
            elif join_mute[1][1] == "VMUTE":
                embed = await EmbedMute(member, timereason, join_mute[1][2]).member_vmute(Infraction.vmute.value)
            elif join_mute[1][1] == "GMUTE":
                embed = await EmbedMute(member, timereason, join_mute[1][2]).member_gmute(Infraction.gmute.value)
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        await TimeMute().mute(member, join_mute[0].total_seconds(), join_mute[1][1])
