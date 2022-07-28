import sqlite3
import pytz
from datetime import datetime, timedelta

from constants import Infraction, LOGS_TYPE, BOT_ID

from utils.action.converter import time_reason

from utils.sql.create_sanction import sanction_process
from utils.sql.get_log import get_logs_moderation

from utils.action.timed_mute import TimeMute

from embed.cogs.embedMute import EmbedMute


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


async def automod_mute_sanction(client, guild, member, type_, check_pun):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute("""
    SELECT COUNT(Sanction.id)
    FROM Sanction
    INNER JOIN Guild
    ON Sanction.guild_id = Guild.id
    WHERE sanction_user_id = ? AND Guild.id = ? AND sanction_ref = ? AND sanction_type = 'MUTE'
    """, (member.id, guild.id, type_))

    time_multiplier = cursor.fetchall()
    time_multiplier = 1 if not time_multiplier else time_multiplier[0][0] + 1

    cursor.execute("""
    SELECT Sanction.id, Sanction.punished
    FROM Sanction
    INNER JOIN Guild
    ON Sanction.guild_id = Guild.id
    WHERE Sanction.sanction_user_id = ? AND Guild.id = ? AND Sanction.sanction_ref = ?
    ORDER BY Sanction.id DESC
    LIMIT ?
    ;
    """, (member.id, guild.id, type_, check_pun[1]))

    last_punishments = cursor.fetchall()
    if not last_punishments:
        last_punishments = (None, True)

    if (
            not any(i[1] for i in last_punishments)
            and len(last_punishments) == check_pun[1]
    ):

        cursor.executemany("""
        UPDATE Sanction
        SET punished = 1
        WHERE id = ?
        ;
        """, [(pun_id,) for pun_id in [i[0] for i in last_punishments]])
        close_connexion(connexion)

        bot_user = await client.fetch_user(BOT_ID)
        tz = pytz.timezone('Europe/Paris')

        sanction_id = await sanction_process(guild.id, "MUTE", f"Trop d'avertissement: {type_}", BOT_ID, member.id,
                                             type_, 0, (datetime.now(tz) + timedelta(seconds=check_pun[0] * time_multiplier)).strftime(r"%Y-%m-%d %H:%M:%S"))

        log_channel_pun = await get_logs_moderation(guild, LOGS_TYPE["sanction"])

        if log_channel_pun:
            reason = await time_reason(check_pun[0] * time_multiplier)
            embed = await EmbedMute(member, bot_user, f"Trop d'avertissement: {type_}",
                                    reason, sanction_id).member_mute(
                Infraction.mute.value)
            await log_channel_pun.send(embed=embed)

        await TimeMute.mute(member, check_pun[0] * time_multiplier, 'Mute')

    else:
        close_connexion(connexion)
