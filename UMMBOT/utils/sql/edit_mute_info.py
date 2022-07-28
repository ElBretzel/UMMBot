import sqlite3


async def update_mute(sanction_id):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute("""
    UPDATE Sanction
    SET punished = 1
    WHERE Sanction.id = ?    
    """,(sanction_id,))

    connexion.commit()
    connexion.close()
