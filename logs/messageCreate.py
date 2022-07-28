from discord.ext import commands
import discord
import sqlite3
import asyncio

from constants import Role, Guild_Info

from rules.badwordsMessage import CheckBadWords
from rules.blockMention import RuleBlockMention
from rules.capsMessage import RuleCapsMessage
from rules.emoteFlood import RuleEmoteFlood
from rules.letterFlood import RuleLetterFlood
from rules.linkMessage import DetectLink
from rules.massMention import RuleMassMention
from rules.spamEmote import RuleSpamEmote
from rules.spamMention import RuleSpamMention
from rules.spamMessage import RuleSpamMessage
from rules.spoilerMessage import RuleSpoilerMessage
from rules.wordFlood import RuleWordFlood
from rules.roleMention import RuleMention
from rules.attachmentMessage import AttachMessage

from utils.action.timed_mute import TimeMute


def close_connexion(connexion):
    connexion.commit()
    connexion.close()


class EventMessageCreate(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.type != discord.MessageType.default:
            return

        member = message.author
        if member.bot:
            return

        channel = message.channel
        if channel.type in [discord.ChannelType.private, discord.ChannelType.group,
                            discord.ChannelType.store]:
            return

        guild = channel.guild
        if guild.id not in Guild_Info.umm_whitelist:
            return

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        cursor.execute("""
        SELECT Logs.message_create
        FROM Logs
        INNER JOIN Guild
        ON Logs.id = Guild.id
        WHERE Guild.id = ?
        ;
        """, (guild.id,))
        log_authorization = cursor.fetchall()[0][0]

        if log_authorization:

            cursor.execute("""
            SELECT Channel.id
            FROM Channel
            INNER JOIN Guild
            ON Channel.guild_id = Guild.id
            WHERE Guild.id = ? AND Channel.logs_message = 1
            ;
            """, (guild.id,))
            log_channel_id = cursor.fetchall()
            log_channel_id = False if not log_channel_id else log_channel_id[0][0]
        else:
            log_channel_id = False

        cursor.execute("""
        SELECT Channel.id
        FROM Channel
        INNER JOIN Guild
        ON Channel.guild_id = Guild.id
        WHERE Guild.id = ?
        GROUP BY Channel.id
        HAVING logs_admin = 1 OR logs_voice = 1 OR logs_sanction = 1 OR logs_message = 1
        ;
        """, (guild.id,))

        logs_channels = cursor.fetchall()

        log_channels = [] if not logs_channels else logs_channels[0]

        if channel.id in log_channels:
            close_connexion(connexion)
            return

        roles = Role(member.roles)
        role_perms = roles.permissions_ if hasattr(roles, 'role') else []

        for role in role_perms:
            if role["manage_guild"] or role['administrator'] or role['manage_messages']:
                close_connexion(connexion)
                return

        close_connexion(connexion)
        if member.id != guild.owner.id:

            tasks = [RuleSpamMessage, RuleSpamEmote, RuleSpamMention,
                     CheckBadWords, RuleBlockMention, RuleMassMention,
                     RuleMention, RuleEmoteFlood, RuleWordFlood, DetectLink, RuleSpoilerMessage,
                     RuleCapsMessage, RuleLetterFlood, AttachMessage]
            tasks = tuple(t(self.client, message) for t in tasks)

            results = [await tasks[0].spam_messages,
                       await tasks[1].spam_emotes,
                       await tasks[2].spam_mentions]
            if all(isinstance(i, type(None)) for i in results):
                func = [tasks[3].spellcheck, tasks[4].block_mention, tasks[5].mass_mention, tasks[6].role_mention,
                        tasks[7].flood_emotes, tasks[8].flood_word, tasks[9].message_link, tasks[10].message_spoiler,
                        tasks[11].message_caps, tasks[12].flood_letter, tasks[13].msg_attach]

                results.extend(await asyncio.gather(*func))

            for index, result in enumerate(results):
                if result:
                    await asyncio.gather(tasks[index].rule_break(member, channel, log_channel_id, result, "m"),
                                         TimeMute().mute(member, 15, "TMute"))
                    break


def setup(client):
    client.add_cog(EventMessageCreate(client))
