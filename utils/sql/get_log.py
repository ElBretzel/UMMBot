import sqlite3


async def get_logs_moderation(guild, log_type):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute(f"""
    SELECT Channel.id
    FROM Channel
    INNER JOIN Guild
    ON Channel.guild_id = Guild.id
    WHERE Guild.id = ? AND {log_type} = 1
    """, (guild.id,))

    channel = cursor.fetchall()

    connexion.close()
    if not channel:
        return

    return guild.get_channel(channel[0][0])
