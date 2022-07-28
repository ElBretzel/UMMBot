import sqlite3
import pytz
from datetime import datetime

from utils.action.timed_mute import TimeMute, TimeUnmute


async def checkup(client):
    tz = pytz.timezone('Europe/Paris')
    date = datetime.now(tz)

    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute("""
    SELECT Guild.id
    FROM Guild
    """)
    guild_id = cursor.fetchall()

    for g in guild_id:
        cursor.execute("""
        SELECT Member.member_id
        FROM Member
        WHERE Member.guild_id = ?
        """, (g[0],))
        member_id = cursor.fetchall()

        for m in member_id:

            cursor.execute("""
            SELECT sanction_finish, sanction_type, Sanction.id
            FROM Sanction
            INNER JOIN Guild
            ON Guild.id = guild_id
            WHERE Guild.id = ? AND sanction_user_id = ? AND (sanction_type = 'MUTE' OR sanction_type = 'VMUTE' OR sanction_type = 'GMUTE') AND punished = 0
            ORDER BY Sanction.id DESC
            LIMIT 1
            """, (g[0], m[0]))
            sanction_finish = cursor.fetchone()

            if sanction_finish:
                sanction_time = datetime.strptime(sanction_finish[0], "%Y-%m-%d %H:%M:%S").astimezone(tz)
                guild = await client.fetch_guild(g[0])
                member = await guild.fetch_member(m[0])
                if date < sanction_time:
                    difference = sanction_time - date
                    await TimeMute().mute(member, difference.total_seconds(), sanction_finish[1])
                else:
                    await TimeUnmute().unmute(member)
