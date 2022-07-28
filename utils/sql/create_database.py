import sqlite3
import os

from constants import DIRECTORY

os.chdir(DIRECTORY)


def create_database():
    if not os.path.isfile("database.db"):
        print("Erreur, base de donnée innexistante!")
        print("Création de la base de donnée, veillez patienter quelques secondes...")
        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Guild (
        id INTEGER PRIMARY KEY NOT NULL,
        whitelisted BOOL DEFAULT 0 NOT NULL
        )
        ;      
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY NOT NULL
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Member (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        guild_id INTEGER NOT NULL, 
        is_blocked BOOL DEFAULT 0 NOT NULL,
        private_owner BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES Guild(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES User(id)
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Automoderation (
        id INTEGER PRIMARY KEY NOT NULL,
        spam_message BOOL DEFAULT 1 NOT NULL,
        spam_mention BOOL DEFAULT 1 NOT NULL,
        spam_emote BOOL DEFAULT 1 NOT NULL,
        block_mention BOOL DEFAULT 1 NOT NULL,
        mass_mention BOOL DEFAULT 1 NOT NULL,
        caps_message BOOL DEFAULT 1 NOT NULL,
        spoil_message BOOL DEFAULT 1 NOT NULL,
        flood_word BOOL DEFAULT 1 NOT NULL,
        flood_letter BOOL DEFAULT 1 NOT NULL,
        flood_emote BOOL DEFAULT 1 NOT NULL,
        role_mention BOOL DEFAULT 1 NOT NULL,
        msg_attachment BOOL DEFAULT 1 NOT NULL,
        bw_message BOOL DEFAULT 1 NOT NULL,
        link_message BOOL DEFAULT 1 NOT NULL,
        FOREIGN KEY (id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ; 
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Mod_Action (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        action_ TEXT NOT NULL,
        type TEXT DEFAULT 'BOT' NOT NULL,
        timestamp DATETIME DEFAULT (datetime('now','localtime')) NOT NULL,
        FOREIGN KEY(guild_id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RSpam_Message (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        distance INTEGER DEFAULT 2 NOT NULL,
        interval INTEGER DEFAULT 3 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RSpam_Mention (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        distance INTEGER DEFAULT 1 NOT NULL,
        interval INTEGER DEFAULT 10 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RSpam_Emote (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        distance INTEGER DEFAULT 2 NOT NULL,
        interval INTEGER DEFAULT 10 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RMass_Mention (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        limite INTEGER DEFAULT 2 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ; 
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RCaps_Message (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        limite INTEGER DEFAULT 4 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RFlood_Word (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        limite INTEGER DEFAULT 2 NOT NULL,
        distance INTEGER DEFAULT 2 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RFlood_Letter (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        limite INTEGER DEFAULT 4 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RFlood_Emote (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        limite INTEGER DEFAULT 2 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RLink_Message (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Link_Info (
        id INTEGER NOT NULL,
        word TEXT,
        state TEXT DEFAULT 'whitelist' NOT NULL,
        FOREIGN KEY (id) REFERENCES RLink_Message(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RBadword_Message(
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        use_french_bw BOOL DEFAULT 1 NOT NULL,
        use_english_bw BOOL DEFAULT 0 NOT NULL,
        use_custom_bw BOOL DEFAULT 1 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Custom_Badwords (
        id INTEGER NOT NULL,
        word TEXT,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RBlock_Mention (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RSpoil_Message (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RRole_Mention (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;      
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RAttach_Message (
        id INTEGER PRIMARY KEY NOT NULL,
        activate BOOL DEFAULT 1 NOT NULL,
        nbefore_mute INTEGER DEFAULT 3 NOT NULL,
        timemute INTEGER DEFAULT 3600 NOT NULL,
        FOREIGN KEY(id) REFERENCES Automoderation(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Entry (
        id INTEGER PRIMARY KEY NOT NULL,
        entry_d_id INTEGER DEFAULT 0,
        d_number TEXT DEFAULT '0',
        entry_m_id INTEGER DEFAULT 0,
        m_number TEXT DEFAULT '0',
        FOREIGN KEY (id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Channel (
        id INTEGER PRIMARY KEY NOT NULL,
        guild_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        logs_message BOOL DEFAULT 0 NOT NULL,
        logs_voice BOOL DEFAULT 0 NOT NULL,
        logs_sanction BOOL DEFAULT 0 NOT NULL,
        logs_admin BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vocal_Channel (
        id INTEGER PRIMARY KEY NOT NULL,
        generator BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (id) REFERENCES Channel(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Text_Channel (
        id INTEGER PRIMARY KEY NOT NULL,
        spam_message BOOL DEFAULT 1 NOT NULL,
        spam_mention BOOL DEFAULT 1 NOT NULL,
        spam_emote BOOL DEFAULT 1 NOT NULL,
        flood_letter BOOL DEFAULT 1 NOT NULL,
        flood_word BOOL DEFAULT 1 NOT NULL,
        flood_emote BOOL DEFAULT 1 NOT NULL,
        block_mention BOOL DEFAULT 1 NOT NULL,
        role_mention BOOL DEFAULT 1 NOT NULL,
        mass_mention BOOL DEFAULT 1 NOT NULL,
        caps_message BOOL DEFAULT 1 NOT NULL,
        spoil_message BOOL DEFAULT 1 NOT NULL,
        msg_attachment BOOL DEFAULT 1 NOT NULL,
        bw_message BOOL DEFAULT 1 NOT NULL,
        link_message BOOL DEFAULT 1 NOT NULL,
        FOREIGN KEY (id) REFERENCES Channel(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Role (
        id INTEGER PRIMARY KEY NOT NULL,
        guild_id INTEGER NOT NULL,
        tmute BOOL DEFAULT 0 NOT NULL,
        mute BOOL DEFAULT 0 NOT NULL,
        vmute BOOL DEFAULT 0 NOT NULL,
        gmute BOOL DEFAULT 0 NOT NULL,
        admin BOOL DEFAULT 0 NOT NULL,
        moderation BOOL DEFAULT 0 NOT NULL,
        animation BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Category_Channel (
        id INTEGER PRIMARY KEY NOT NULL,
        private_category BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (id) REFERENCES Channel(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Private_Channel (
        id INTEGER PRIMARY KEY NOT NULL,
        id_voice INTEGER NOT NULL,
        id_text INTEGER NOT NULL,
        FOREIGN KEY (id) REFERENCES Member(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Private_Participants (
        id INTEGER NOT NULL,
        participant_id INTEGER DEFAULT 0,
        FOREIGN KEY (id) REFERENCES Private_Channel (id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Logs (
        id INTEGER PRIMARY KEY NOT NULL,
        member_ban BOOL DEFAULT 1 NOT NULL,
        member_join BOOL DEFAULT 1 NOT NULL,
        member_kick BOOL DEFAULT 1 NOT NULL,
        member_leave BOOL DEFAULT 1 NOT NULL,
        member_update BOOL DEFAULT 1 NOT NULL,
        user_update BOOL DEFAULT 1 NOT NULL,
        add_reaction BOOL DEFAULT 0 NOT NULL,
        message_create BOOL DEFAULT 1 NOT NULL,
        message_delete BOOL DEFAULT 1 NOT NULL,
        message_edit BOOL DEFAULT 1 NOT NULL,
        remove_react BOOL DEFAULT 0 NOT NULL,
        voice_connect BOOL DEFAULT 1 NOT NULL,
        voice_selfupdate BOOL DEFAULT 1 NOT NULL,
        voice_switch BOOL DEFAULT 1 NOT NULL,
        voice_update BOOL DEFAULT 1 NOT NULL,
        FOREIGN KEY(id) REFERENCES Guild (id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sanction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        sanction_type TEXT NOT NULL,
        sanction_description TEXT NOT NULL,
        sanction_mod_id INT NOT NULL,
        sanction_user_id INT NOT NULL,
        sanction_ref TXT NOT NULL,
        sanction_create DATETIME DEFAULT (datetime('now','localtime')) NOT NULL,
        sanction_finish DATETIME DEFAULT (datetime('now','localtime')) NOT NULL,
        punished BOOL DEFAULT 0 NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES Guild(id) ON DELETE CASCADE
        )
        ;
        """)
        connexion.commit()
        print("Effectué!")


if __name__ == "__main__":
    create_database()
