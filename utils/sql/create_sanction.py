import sqlite3


async def sanction_process(guild_id, sanction_type, reason, mod_id, user_id, sanction_ref, punished, sanction_finish=None):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    if sanction_finish:
        cursor.execute("""
        INSERT INTO Sanction ( guild_id, sanction_type, sanction_description, sanction_mod_id, sanction_user_id, sanction_ref, sanction_finish, punished)
        VALUES ( ?, ?, ?, ?, ?, ?, ?, ?)
        ;
        """, (guild_id, sanction_type, reason, mod_id, user_id, sanction_ref, sanction_finish, punished))
    else:
        cursor.execute("""
        INSERT INTO Sanction ( guild_id, sanction_type, sanction_description, sanction_mod_id, sanction_user_id, sanction_ref, punished)
        VALUES ( ?, ?, ?, ?, ?, ?, ?)
        ;
        """, (guild_id, sanction_type, reason, mod_id, user_id, sanction_ref, punished))
    connexion.commit()

    cursor.execute("""
    SELECT Sanction.id
    FROM Sanction
    INNER JOIN Guild
    ON Sanction.guild_id = Guild.id
    WHERE Guild.id = ? and sanction_user_id = ?
    ORDER BY Sanction.id DESC
    LIMIT 1;
    """, (guild_id, user_id))
    result = cursor.fetchall()[0][0]
    connexion.close()

    return result

