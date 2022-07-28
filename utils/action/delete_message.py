import sqlite3

from constants import BOT_ID


async def delete_message(ctx):
    delete_message_sql(ctx.guild.id, ctx.author.id)
    await ctx.message.delete()


def delete_message_sql(guild_id, author_id):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()
    cursor.execute("""
    INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
    VALUES ( ?, ?, ?, ?, ? )
    ;     
    """, (guild_id, BOT_ID, author_id, "DELETE", "BOT"))

    connexion.commit()
    connexion.close()
