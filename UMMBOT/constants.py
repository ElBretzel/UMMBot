import discord
import logging
from datetime import timezone, timedelta, datetime
import os
import sys
from enum import Enum


class TimeZone:
    @staticmethod
    def utc_to_local(utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


class Logger:
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


class Attachment(Logger):
    def __init__(self, file):
        self.file = file

    @property
    def check_extension_(self):
        """
        Check if the attachment's extension is blocked by the bot
        :return: str
        """
        block_extension = ['exe', 'bat', 'com', 'dll', 'vbs', 'xls',
                           'doc', 'docx', 'xlsx', 'jar', 'js', 'htm',
                           'html', 'hta', 'vb', 'pdf', 'sfx', 'tmp',
                           'py', 'msi', 'msp', 'com', 'gadget', 'cmd',
                           'vbe', 'jse', 'ps1', 'ps1xml', 'ps2', 'ps2xml',
                           'psc1', 'psc2', 'lnk', 'inf', 'scf', 'rar', 'zip']
        file_ext = os.path.splitext(self.file.filename)
        if file_ext[1].strip(".") in block_extension:
            logging.warning(f"Le fichier {self.file.filename} a une extension incorrecte")
            return file_ext[1]
        else:
            logging.info(f"Le fichier attaché {self.file.filename} semble correcte")

    @property
    def id_(self):
        """

        :return: int
        """
        logging.info(f"ID du fichier {self.file.filename}: {self.file.id}")
        return self.file.id

    @property
    def size_(self):
        """
        Convert the size of the file from bytes to ko
        :return: int
        """
        size = self.file.size * (10 ** - 3)
        logging.info(f"Taille du fichier {self.file.filename}: {size}")
        return size

    @property
    def name_(self):
        """

        :return: str
        """
        logging.info(f"Nom du fichier: {self.file.filename}")
        return self.file.filename

    @property
    def url_(self):
        """

        :return: str
        """
        logging.info(f"URL du fichier {self.file.filename}: {self.file.url}")
        return self.file.url

    @property
    def spoiler_(self):
        """
        Check if the file is in a spoiler
        :return: bool
        """
        if self.file.is_spoiler():
            logging.info(f"Fichier {self.file.filename} sous spoiler: {self.file.is_spoiler()}")
            return True
        else:
            logging.warning(f"Le fichier {self.file.filename} ne contient pas de spoiler.")
            return False


class VoiceState(Logger):

    @staticmethod
    def voicestate(voice):
        return {"deaf": voice.deaf,
                "mute": voice.mute,
                "self_deaf": voice.self_deaf,
                "self_mute": voice.self_mute,
                "channel": voice.channel}


class Role(Logger):
    def __init__(self, role):
        self.role = role

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if value:
            self._role = value
        else:
            logging.warning(f"Le rôle est un rôle @everyone")

    @property
    def name_(self):
        """

        :return: str
        """
        logging.info(f"L'activité a le nom {self.role.name}")
        return self.role.name

    @property
    def id_(self):
        """
        :return: int
        """
        logging.info(f"ID du rôle {self.role.id}")
        return self.role.id

    @property
    def guild_(self):
        """

        :return: Guild
        """
        logging.info(f"Le rôle {self.role.id} appartient à la guilde {self.role.guild.id}")
        return self.role.guild

    @property
    def permissions_(self):
        """

        :return: Dict[bool]
        """
        logging.info(f"Génération des permissions des roles {self.role}")
        perms = [i.permissions for i in self.role]
        return [
            {
                "create_instant_invite": perms[i].create_instant_invite,
                "kick_members": perms[i].kick_members,
                "ban_members": perms[i].ban_members,
                "administrator": perms[i].administrator,
                "manage_channels": perms[i].manage_channels,
                "manage_guild": perms[i].manage_guild,
                "add_reactions": perms[i].add_reactions,
                "view_audit_log": perms[i].view_audit_log,
                "priority_speaker": perms[i].priority_speaker,
                "stream": perms[i].stream,
                "read_messages": perms[i].read_messages,
                "send_messages": perms[i].send_messages,
                "send_tts_messages": perms[i].send_tts_messages,
                "manage_messages": perms[i].manage_messages,
                "embed_links": perms[i].embed_links,
                "attach_files": perms[i].attach_files,
                "read_message_history": perms[i].read_message_history,
                "mention_everyone": perms[i].mention_everyone,
                "external_emojis": perms[i].external_emojis,
                "view_guild_insights": perms[i].view_guild_insights,
                "connect": perms[i].connect,
                "speak": perms[i].speak,
                "mute_members": perms[i].mute_members,
                "deafen_members": perms[i].deafen_members,
                "move_members": perms[i].move_members,
                "use_voice_activation": perms[i].use_voice_activation,
                "change_nickname": perms[i].change_nickname,
                "manage_nicknames": perms[i].manage_nicknames,
                "manage_roles": perms[i].manage_roles,
                "manage_webhooks": perms[i].manage_webhooks,
                "manage_emojis": perms[i].manage_emojis,
            }
            for i in range(len(perms))
        ]

    @property
    def members_(self):
        """

        :return: List[Member]
        """
        logging.info(f"Génération de la liste des membres du rôle {self.role.id}")
        return self.role.members


class Invite(Logger):
    def __init__(self, invite):
        self.invite = invite

    @property
    def max_(self):
        """
        Time in seconds
        :return: Tuple(int)
        """
        if self.invite.max_age == 0:
            logging.info(f"L'invitation {self.invite.id} s'expire jamais")
            return tuple(0)
        else:
            time_max = timedelta(seconds=self.invite.max_age)
            tm = time_max.seconds
            days, hours, minutes, seconds = (tm // (3600 * 24)), (tm // 3600) % 24, (tm // 60) % 60, (tm % 60)
            logging.info(f"L'invitation {self.invite.id} à été créer il y a {days} jours, {hours}:{minutes}:{seconds}")
            return tuple(days, hours, minutes, seconds, )

    @property
    def code_(self):
        """

        :return: str
        """
        logging.info(f"Code de l'invitation {self.invite.id}: {self.invite.code}")
        return self.invite.code

    @property
    def guild_(self):
        """

        :return: PartialInviteGuild
        """
        logging.info(f"L'invitation {self.invite.id} vient de la guilde {self.invite.guild}")
        return self.invite.guild

    @property
    def creation_(self):
        """
        Transform datetime UTC to local UTC
        :return: datetime.datetime
        """
        time = self.invite.created_at
        time = TimeZone.utc_to_local(utc_dt=time)
        logging.info(f"Création de l'invitation {self.invite.id}: {time}")
        return time

    @property
    def uses_(self):
        """

        :return: int
        """
        logging.info(f"L'invitation {self.invite.id} à été utilisé {self.invite.uses}")
        return self.invite.uses

    @property
    def inviter_(self):
        """

        :return: User
        """
        logging.info(f"L'invitation {self.invite.id} à été créer par {self.invite.inviter.id}")
        return self.invite.inviter

    @property
    def channel_(self):
        """

        :return: PartialInviteChannel
        """
        logging.info(f"L'invitation {self.invite.id} redirige vers le salon {self.invite.channel.id}")
        return self.invite.channel


class Infraction(Enum):
    wars = discord.Color.orange()
    kick = discord.Color.gold()
    ban = discord.Color.orange()
    delete = discord.Color.dark_blue()
    mute = discord.Color.blue()
    vmute = discord.Color.purple()
    gmute = discord.Color.blurple()


class Infos(Enum):
    default = discord.Color.lighter_grey()
    success = discord.Color.green()
    error = discord.Color.red()
    warning = discord.Color.orange()
    unknown = discord.Color.dark_red()
    permissions = discord.Color.gold()


class Guild_Info:
    umm_whitelist = [356462658427551744, 672867622731251739, 728745118701584465]


class Sanction_Type(Enum):
    ban = "BAN"
    kick = "KICK"
    mute = "MUTE"
    vmute = "VMUTE"
    gmute = "GMUTE"
    warn = "WARN"


LOGS_TYPE = {"moderation": "logs_admin",
             "message": "logs_message",
             "voice": "logs_voice",
             "sanction": "logs_sanction"}

PREFIX = "&"

OS_SLASH = "\\" if sys.platform == "win32" else "/"

BLOCK_EMOTE = '<:blocked:740272074521837579>'

OWNER = "Bretzel_#2246"

HELP_CATEGORY = {"developpement": ["developpement", "dev"],
                 "administration": ["administration", "admin"],
                 "moderation": ["moderation", "mod"],
                 "animation": ["animation", "anim"],
                 "utilitaire": ["utilitaire", "utils"],
                 "musique": ["musique", "music"],
                 "fun": ["fun"]
                 }

RULES = {"spam_message": "Spam message", "spam_mention": "Spam mention", "spam_emote": "Spam emote",
         "flood_letter": "Flood de lettre", "flood_word": "Flood de mot", "flood_emote": "Flood d'emote",
         "block_mention": "Mention bloquée", "role_mention": "Mention de rôle", "caps_message": "Message en majuscule",
         "spoil_message": "Spoiler", "msg_attachment": "Message attaché", "bw_message": "Mot interdit",
         "link_message": "Lien interdit", "mass_mention": "Mention de masse"}

RULES_AUTOMOD = {"spam_message": "RSpam_Message",
                 "spam_mention": "RSpam_Mention",
                 "spam_emote": "RSpam_Emote",
                 "block_mention": "RBlock_Mention",
                 "mass_mention": "RMass_Mention",
                 "caps_message": "RCaps_Message",
                 "spoil_message": "RSpoil_Message",
                 "flood_word": "RFlood_Word",
                 "flood_letter": "RFlood_Letter",
                 "flood_emote": "RFlood_Emote",
                 "role_mention": "RRole_Mention",
                 "msg_attachment": "RAttach_Message",
                 "bw_message": "RBadword_Message",
                 "link_message": "RLink_Message"}

CONFIG_AUTOMOD = {"timemute": "Temps de mute (multiplié par le nombre de mute du même type):",
                  "nbefore_mute": "Nombre d'avertissements avant mute:",
                  "use_french_bw": "Utilisation du dictionnaire francais:",
                  "use_english_bw": "Utilisation du dictionnaire anglais:",
                  "use_custom_bw": "Utilisation du dictionnaire custom:",
                  "limite": "Nombre autorisé de détection avant avertissement:",
                  "distance": "Distance de vérification entre X messages/mots:",
                  "check_msg": "Nombre de messages vérifiés par le bot:",
                  "interval": "Intervalle de messages avant avertissement:"}

LOGS = {"member_ban": "Membre banni", "member_join": "Nouveau membre", "member_kick": "Membre kick",
        "member_leave": "Membre parti", "member_update": "Membre mis-à-jour", "user_update": "Utilisateur mis-à-jour",
        "add_reaction": "Réaction ajoutée", "message_create": "Message crée", "message_edit": "Message édité",
        "remove_react": "Réaction supprimée", "voice_connect": "Connection vocale",
        "voice_selfupdate": "Statut vocal mis-à-jour",
        "voice_switch": "Changement de salon", "voice_update": "Changement forcé de statut vocal",
        "message_delete": "Message supprimé"}

CHANNEL_LOG = {"logs_message": "Logs messages",
               "logs_voice": "Logs vocaux",
               "logs_admin": "Logs modération",
               "logs_sanction": "Logs sanctions"
               }

HELP_REACTION = ("🚧", "📯", "⚖", "🎏", "💎", "🥁", "🎭", "⬅", "⏪", "❌")
SANCTION_REACTION_MAIN = {"WARN": "💣",
                          "MUTE": "🎙",
                          "KICK": "⏳",
                          "BAN": "🔨",
                          "cancel": "❌"}

SANCTION_TYPE_ID = {"WARN": 1,
                    "KICK": 2,
                    "BAN": 3,
                    "MUTE": 4,
                    "VMUTE": 5,
                    "GMUTE": 6}

BOT_ID = 677213520529457152

GENID_CREATION = datetime.strptime("2020-08-10 18:00:00", '%Y-%m-%d %H:%M:%S')

DIRECTORY = os.path.abspath("")
