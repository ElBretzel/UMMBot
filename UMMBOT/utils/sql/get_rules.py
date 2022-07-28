import sqlite3

from constants import RULES_AUTOMOD


async def get_automoderation_rules(guild, rule):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    rule = RULES_AUTOMOD.get(rule)

    cursor.execute(f"""
    SELECT *
    FROM {rule}
    WHERE {rule}.id = ?
    """, (guild.id,))

    description = [description[0] for description in cursor.description]
    data = cursor.fetchall()
    connexion.close()

    return data, description
