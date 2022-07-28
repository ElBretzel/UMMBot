import sqlite3
import os
from constants import DIRECTORY

os.chdir(DIRECTORY)


def leave_guild(guild):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    query = f"""
    DELETE FROM Guild
    WHERE id = {guild.id}
    ;
    """
    cursor.execute("PRAGMA foreign_keys = ON")
    connexion.commit()
    cursor.execute(query)
    connexion.commit()
    connexion.close()
