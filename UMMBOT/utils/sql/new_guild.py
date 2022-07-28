import sqlite3
import os
from constants import DIRECTORY

os.chdir(DIRECTORY)


def new_guild(guild):
    guild_info = {
        "list_member": [(i.id, guild.id) for i in guild.members],
        "list_roles": [(i.id, guild.id) for i in guild.roles],
        "list_voc_channel": [(i.id, guild.id) for i in guild.voice_channels],
        "list_txt_channel": [(i.id, guild.id) for i in guild.text_channels],
        "list_cat_channel": [(i.id, guild.id) for i in guild.categories],
        "guild_id": guild.id
    }

    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute("INSERT INTO Guild ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO Entry ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO Automoderation ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO Logs ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RBadword_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RCaps_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RFlood_Emote ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RFlood_Letter ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RFlood_Word ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RLink_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RMass_Mention ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RSpam_Emote ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RSpam_Mention ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RSpam_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RBlock_Mention ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RSpoil_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RRole_Mention ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()
    cursor.execute("INSERT INTO RAttach_Message ( id ) VALUES ( :guild_id );", guild_info)
    connexion.commit()

    cursor.executemany("INSERT INTO Member ( member_id, guild_id ) VALUES ( ?, ? );", guild_info["list_member"])
    connexion.commit()

    cursor.executemany("""INSERT INTO User ( id ) SELECT ?
                          WHERE NOT EXISTS (SELECT id FROM User WHERE id = ? );""", [(i.id, i.id) for i in guild.members])
    connexion.commit()

    cursor.executemany("INSERT INTO Role ( id, guild_id ) VALUES ( ?, ? );", guild_info["list_roles"])
    connexion.commit()

    cursor.executemany("INSERT INTO Channel ( id, guild_id, type ) VALUES ( ?, ?, 'VOC' );",
                       guild_info["list_voc_channel"])
    connexion.commit()

    cursor.executemany("INSERT INTO Vocal_Channel ( id ) VALUES ( ? );",
                       [(i.id,) for i in guild.voice_channels])
    connexion.commit()

    cursor.executemany("INSERT INTO Channel ( id, guild_id, type ) VALUES ( ?, ?, 'TXT' );",
                       guild_info["list_txt_channel"])
    connexion.commit()

    cursor.executemany("INSERT INTO Text_Channel ( id ) VALUES ( ? );",
                       [(i.id,) for i in guild.text_channels])
    connexion.commit()

    cursor.executemany("INSERT INTO Channel ( id, guild_id, type ) VALUES ( ?, ?, 'CAT' );",
                       guild_info["list_cat_channel"])
    connexion.commit()

    cursor.executemany("INSERT INTO Category_Channel ( id ) VALUES ( ? );",
                       [(i.id,) for i in guild.categories])
    connexion.commit()

    connexion.close()

    print(f"Guild ({guild.id}) db created")
