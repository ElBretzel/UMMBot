from json import load
from spellchecker import SpellChecker
import sqlite3
from datetime import datetime
import pytz

from embed.rules.embedBadwords import Embed

from utils.sql.rules_automod import automod_mute_sanction
from utils.sql.create_sanction import sanction_process

from embed.logs.embedQuitAndMute import EmbedMute

from utils.action.converter import time_reason
from utils.action.timed_mute import TimeMute

from constants import Infraction


def french_bw():
    with open("french_bw.json", "r") as f:
        return load(f)


def english_bw():
    with open("english_bw.json", "r") as f:
        return load(f)


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class CheckBadWords:
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
- Nous avons détecté dans votre dernier message un ou plusieurs mots offensants et / ou interdits par l'administrateur du serveur. 
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

    @staticmethod
    async def generator_w(misspelled, spell, list_bw):
        for m in misspelled:
            for b in list_bw:
                str_b = {k for k in b.lower()}
                str_m = {k for k in m}
                if not len(str_m) - 1 <= len(str_b) <= len(str_m) + 1:
                    continue
                str_bm = []
                i = 0
                for k in str_m:
                    if k in str_b:
                        str_bm.append(k)
                    else:
                        i += 1
                    if i == 2:
                        break
                if len(str_b) - 1 <= len(str_bm) <= len(str_b) + 1:
                    a = spell.correction(m)
                    if a in list_bw:
                        yield a, m
                        break

    @staticmethod
    async def generator_y(know, list_bw):
        for k in know:
            if k in list_bw:
                yield k

    @property
    async def spellcheck(self):

        if self.args:
            guild = self.args[0]
            message_content = self.message
        else:
            guild = self.message.guild
            channel = self.message.channel
            message_content = self.message.content

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RBadword_Message.activate, use_french_bw, use_english_bw, use_custom_bw
        FROM RBadword_Message
        INNER JOIN Guild
        ON RBadword_Message.id = Guild.id
        WHERE Guild.id = ?
        """, (guild.id,))

        check_badwords = cursor.fetchall()[0]

        if not self.args:
            cursor.execute("""
            SELECT Text_Channel.bw_message
            FROM Text_Channel
            INNER JOIN Channel
            ON Text_Channel.id = Channel.id
            WHERE Channel.id = ?
            ; 
            """, (channel.id,))

            chan_authorization = cursor.fetchall()[0][0]
        else:
            chan_authorization = True

        if not check_badwords[0] or not chan_authorization:
            close_connexion(connexion)
            return

        spell = SpellChecker(distance=1, language="fr")

        list_bw = []

        if check_badwords[1]:
            list_bw += french_bw()
            spell.word_frequency.load_text_file(r"utils/misc/french_bw.txt")
        if check_badwords[2]:
            list_bw += english_bw()
            spell.word_frequency.load_text_file(r"utils/misc/english_bw.txt")
        if check_badwords[3]:
            cursor.execute("""
            SELECT Custom_Badwords.word
            FROM Custom_Badwords
            INNER JOIN RBadword_Message
            ON Custom_Badwords.id = RBadword_Message.id
            WHERE RBadword_Message.id = ?
            """, (guild.id,))
            custom_bw = cursor.fetchall()

            if custom_bw:
                custom_bw = [i[0].lower() for i in custom_bw]
                spell.word_frequency.load_words(custom_bw)
                list_bw += custom_bw

        replacement = (',', '.', '?', '!', '/', ':', ';', '||', '|')
        msg = list(set(message_content.lower().replace('\n', ' ').split(' ')))
        for n, m in enumerate(msg):
            if len(m) <= 1:
                msg.pop(n)
                continue
            elif m.isdigit():
                msg.pop(n)
                continue
            for r in replacement:
                if m.endswith(r) or m.startswith(r):
                    msg[n] = m.replace(r, '')
                    continue

        know = spell.known(msg)
        misspelled = spell.unknown(msg)
        potential = set()
        certain = set()

        async for i in self.generator_w(misspelled, spell, list_bw):
            potential.add(i)
        async for j in self.generator_y(know, list_bw):
            certain.add(j)

        close_connexion(connexion)
        if not potential and not certain:
            return
        return potential, certain

    async def rule_break(self, member, channel, log_channel_id, result, *args):
        detection_type = args[0]
        if result[1]:
            message_detection = ' | '.join(result[1])
        elif result[0]:
            message_detection = ''.join([f"Entrée: {b[1]} | Sortie: {b[0]}\n" for b in result[0]])

        guild = member.guild

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT RBadword_Message.timemute, RBadword_Message.nbefore_mute
        FROM RBadword_Message
        INNER JOIN Guild
        ON RBadword_Message.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        check_pun = cursor.fetchall()[0]

        cursor.execute("""
        SELECT Automoderation.bw_message
        FROM Automoderation
        INNER JOIN Guild
        ON Automoderation.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))

        automod_authorization = cursor.fetchall()[0][0]
        join_mute = None

        sanction_id = None
        if automod_authorization:
            join_mute = await self.warn_process(member, channel, detection_type, cursor, connexion, guild)
            reason = 'Message insultant' if detection_type == "m" else 'Pseudonyme insultant'
            if not join_mute:
                sanction_id = await sanction_process(guild.id, 'WARN', reason, self.client.user.id, member.id,
                                                     'RBADWORDS', 0)

        if log_channel_id and not join_mute:
            embed = Embed(member, channel, self.message, message_detection, detection_type, sanction_id)
            embed = await embed.badwords_embed()
            channel_send = self.client.get_channel(log_channel_id)
            await channel_send.send(embed=embed)

        if automod_authorization and not join_mute:
            await automod_mute_sanction(self.client, guild, member, "RBADWORDS", check_pun)
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
