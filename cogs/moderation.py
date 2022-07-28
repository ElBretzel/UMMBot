from discord.ext import commands
import discord
from datetime import datetime, timedelta
import typing
import pytz

from utils.sql.create_sanction import sanction_process
from utils.sql.get_log import get_logs_moderation
from utils.sql.get_db_info import GetDBInfo
from utils.sql.update_db_command import EditDBPerms

from utils.action.converter import convert_time, time_reason, ErrorConvertionTime
from utils.action.delete_message import delete_message
from utils.action.timed_mute import TimeMute, TimeUnmute

from constants import Infraction, Infos, Sanction_Type, PREFIX, LOGS_TYPE, OWNER, SANCTION_TYPE_ID, GENID_CREATION

from utils.checking.is_moderator import check_if_moderator
from utils.checking.is_whitelisted import check_if_whitelisted, ErrorGuildNotWhitelisted
from utils.checking.is_bot_owner import check_if_bot_owner
from utils.checking.is_administrator import check_if_administrator
from utils.checking.is_higher_rank import check_hierarchy, ErrorMemberLowerRank

from embed.cogs.embedBan import EmbedBan
from embed.cogs.embedKick import EmbedKick
from embed.cogs.embedMute import EmbedMute
from embed.cogs.embedClear import EmbedClear
from embed.cogs.embedUnban import EmbedUnban
from embed.cogs.embedUnmute import EmbedUnmute
from embed.cogs.embedWarn import EmbedWarn

from utils.sanction_command import SanctionCommand

tz = pytz.timezone('Europe/Paris')


class ConvertMember(commands.MemberConverter):
    async def convert(self, ctx, arg):
        member = await super().convert(ctx, arg)
        return member


class ConvertUser(commands.UserConverter):
    async def convert(self, ctx, arg):
        user = await super().convert(ctx, arg)
        return user


class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(description="Supprime définitivement un nombre défini de message (défaut: 5).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(
            embed=discord.Embed(title='Info clear', description=f"{amount} messages ont été supprimés avec succès!",
                                color=Infos.success.value), delete_after=3)

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["moderation"])
        if log_channel:
            embed = await EmbedClear(ctx.channel, amount, ctx.author).clear_message(Infraction.delete.value)
            await log_channel.send(embed=embed)

    @clear.error
    async def clear_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nombre spécifié doit être un entier naturel non nul.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clear""",
                                    color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Banni indéfiniment le membre spécifié. Vous pouvez préciser le "
                                  "nombre de jour auquel les messages du membre seront supprimés définitivement "
                                  "(défaut: 0) ainsi que la raison du bannissement (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def ban(self, ctx, member: ConvertMember, delete_days: typing.Optional[int] = 0,
                  *, reason: typing.Optional[str] = "Raison non spécifiée"):

        await check_hierarchy(ctx, member)
        await member.ban(reason=reason, delete_message_days=delete_days)
        await ctx.send(
            embed=discord.Embed(title='Info ban',
                                description=f"Le membre <@{member.id}> a été banni avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)
        await delete_message(ctx)

        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.ban.value, reason, ctx.author.id, member.id,
                                              "N/A", 1)

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedBan(member, ctx.author, reason, sanction_id).member_ban(Infraction.ban.value)
            await log_channel.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande ban.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help ban""",
                                               color=Infos.error.value), delete_after=10)

        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help ban""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas bannir cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Fait quitter le membre spécifié du serveur de manière non définitive. "
                                  "Vous pouvez préciser une raison (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def kick(self, ctx, member: ConvertMember, *, reason: typing.Optional[str] = "Raison non spécifiée"):

        await check_hierarchy(ctx, member)

        await member.kick(reason=reason)
        await ctx.send(
            embed=discord.Embed(title='Info kick',
                                description=f"Le membre <@{member.id}> a été kick avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)
        await delete_message(ctx)

        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.kick.value, reason, ctx.author.id, member.id,
                                              "N/A", 1)

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedKick(member, ctx.author, reason, sanction_id).member_kick(Infraction.kick.value)
            await log_channel.send(embed=embed)

    @kick.error
    async def kick_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande kick.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help kick""",
                                               color=Infos.error.value), delete_after=10)

        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help kick""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas kick cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(
        description="Rend muet le membre spécifié uniquement dans les salons textuels. Vous pouvez préciser "
                    "la durée au cours duquel le membre restera muet (format: y,mo,w,d,h,min,s) ainsi que la raison "
                    "du mute (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def mute(self, ctx, member: ConvertMember, timeduration: str, *,
                   reason: typing.Optional[str] = "Raison non spécifiée"):

        await check_hierarchy(ctx, member)

        timeduration = await convert_time(timeduration)
        timereason = await time_reason(timeduration)
        await ctx.send(
            embed=discord.Embed(title='Info mute',
                                description=f"Le membre <@{member.id}> a été mute avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)
        await delete_message(ctx)
        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.mute.value, reason, ctx.author.id, member.id,
                                              "N/A", 0, (datetime.now(tz) + timedelta(seconds=timeduration)).strftime(r"%Y-%m-%d %H:%M:%S"))

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedMute(member, ctx.author, reason, timereason, sanction_id).member_mute(
                Infraction.mute.value)
            await log_channel.send(embed=embed)

        await TimeMute().mute(member, timeduration, "Mute", sanction_id)

    @mute.error
    async def mute_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande mute.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mute""",
                                               color=Infos.error.value), delete_after=10)

        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mute""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas mute cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorConvertionTime):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Le format de temps est mal spécifié ( y,mo,w,d,h,min,s ) 
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mute""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(
        description="Rend muet le membre spécifié uniquement dans les salons vocaux. Vous pouvez préciser "
                    "la durée au cours duquel le membre restera muet (format: y,mo,w,d,h,min,s) ainsi que la raison "
                    "du mute (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def vmute(self, ctx, member: ConvertMember, timeduration: str, *,
                    reason: typing.Optional[str] = "Raison non spécifiée"):

        await check_hierarchy(ctx, member)
        timeduration = await convert_time(timeduration)
        timereason = await time_reason(timeduration)

        await ctx.send(
            embed=discord.Embed(title='Info mute',
                                description=f"Le membre <@{member.id}> a été mute vocal avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)
        await delete_message(ctx)

        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.vmute.value, reason, ctx.author.id, member.id,
                                              "N/A", 0, (datetime.now(tz) + timedelta(seconds=timeduration)).strftime(r"%Y-%m-%d %H:%M:%S"))

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedMute(member, ctx.author, reason, timereason, sanction_id).member_vmute(
                Infraction.vmute.value)
            await log_channel.send(embed=embed)

        await TimeMute().mute(member, timeduration, "VMute", sanction_id)

    @vmute.error
    async def vmute_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande vmute.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help vmute""",
                                               color=Infos.error.value), delete_after=10)

        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help vmute""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas mute cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorConvertionTime):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Le format du temps est mal spécifié ( y,mo,w,d,h,min,s ) 
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help vmute""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(
        description="Rend muet le membre spécifié dans les salons textuels et vocaux. Vous pouvez préciser "
                    "la durée au cours duquel le membre restera muet (format: y,mo,w,d,h,min,s) ainsi que la raison "
                    "du mute (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def gmute(self, ctx, member: ConvertMember, timeduration: str,
                    *, reason: typing.Optional[str] = "Raison non spécifiée"):

        await check_hierarchy(ctx, member)
        timeduration = await convert_time(timeduration)
        timereason = await time_reason(timeduration)

        await ctx.send(
            embed=discord.Embed(title='Info mute',
                                description=f"Le membre <@{member.id}> a été mute global avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)
        await delete_message(ctx)

        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.gmute.value, reason, ctx.author.id, member.id,
                                              "N/A", 0, (datetime.now(tz) + timedelta(seconds=timeduration)).strftime(r"%Y-%m-%d %H:%M:%S"))

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedMute(member, ctx.author, reason, timereason, sanction_id).member_gmute(
                Infraction.gmute.value)
            await log_channel.send(embed=embed)

        await TimeMute().mute(member, timeduration, "GMute", sanction_id)
    @gmute.error
    async def gmute_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande gmute.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help gmute""",
                                               color=Infos.error.value), delete_after=10)

        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help gmute""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas mute cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorConvertionTime):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Le format du temps est mal spécifié ( y,mo,w,d,h,min,s ) 
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help gmute""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Enleve le mute du membre spécifié "
                                  "(il est vivement déconseillé d'unmute un membre en lui enlevant uniquement son rôle!). "
                                  "Vous pouvez préciser une raison (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def unmute(self, ctx, member: ConvertMember, *, reason: typing.Optional[str] = "Raison non spécifiée"):

        await delete_message(ctx)
        await TimeUnmute().unmute(member)

        await ctx.send(
            embed=discord.Embed(title='Info unmute',
                                description=f"Le membre <@{member.id}> a été unmute avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedUnmute(member, ctx.author, reason).member_unmute(Infraction.mute.value)
            await log_channel.send(embed=embed)

    @unmute.error
    async def unmute_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande unmute.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help unmute""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help unmute""",
                                    color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, NameError):
                await ctx.send(embed=discord.Embed(title='Attention!',
                                                   description=f"Cet utilisateur n'est pas mute.",
                                                   color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Enleve le bannissement du membre spécifié. "
                                  "Vous pouvez préciser une raison (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def unban(self, ctx, user: ConvertUser, *, reason: typing.Optional[str] = "Raison non spécifiée"):
        await delete_message(ctx)

        banned_users = await ctx.guild.bans()
        for b in banned_users:
            ban_user = b.user
            if ban_user.id == user.id:
                await ctx.guild.unban(user)
                await ctx.send(
                    embed=discord.Embed(title='Info unban',
                                        description=f"L'utilisateur <@{user.id}> a été unban avec succès pour: **{reason}**",
                                        color=Infos.success.value), delete_after=10)
                break
        else:
            raise ValueError

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if not log_channel:
            return

        embed = await EmbedUnban(user, ctx.author, reason).member_unban(Infraction.ban.value)
        await log_channel.send(embed=embed)

    @unban.error
    async def unban_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande unban.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help unban""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help unban""",
                                    color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, ValueError):
                await ctx.send(embed=discord.Embed(title='Attention!',
                                                   description=f"Cet utilisateur n'est pas ban du serveur.",
                                                   color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=["sanction"], description="Affiche la liste des sanctions du membre spécifié")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def sanctions(self, ctx, user: ConvertUser):

        await delete_message(ctx)
        sanctions = await GetDBInfo().info_sanctions(ctx, user)
        command = SanctionCommand(self.client)
        embed = await command.embed_main_menu(ctx, user, sanctions)
        message = await ctx.send(embed=embed, delete_after=60)
        await command.wait_main_reaction(ctx, message, user, sanctions)

    @sanctions.error
    async def sanctions_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande sanctions.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help sanctions""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help sanctions""",
                                    color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Ajoute un avertissement au joueur spécifié"
                                  "Vous pouvez préciser une raison (défaut: Raison non spécifiée).")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def warn(self, ctx, member: ConvertMember, *, reason: typing.Optional[str] = "Raison non spécifiée"):
        await check_hierarchy(ctx, member)
        await delete_message(ctx)

        await ctx.send(
            embed=discord.Embed(title='Info warn',
                                description=f"Le membre <@{member.id}> a été averti avec succès pour: **{reason}**",
                                color=Infos.success.value), delete_after=10)

        sanction_id = await sanction_process(ctx.guild.id, Sanction_Type.warn.value, reason, ctx.author.id, member.id,
                                              "N/A", 1)

        log_channel = await get_logs_moderation(ctx.guild, LOGS_TYPE["sanction"])
        if log_channel:
            embed = await EmbedWarn(member, ctx.author, reason, sanction_id).member_warn(Infraction.mute.value)
            await log_channel.send(embed=embed)

    @warn.error
    async def warn_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande warn.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help warn""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help warn""",
                                    color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, ErrorMemberLowerRank):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous ne pouvez pas warn cet utilisateur (permission manquante).",
                                               color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Vérifie un dossier à partir de l'ID fournit. "
                                  f"Vous pouvez retrouver rapidement la liste des dossiers d'un utilisateur à l'aide "
                                  f"de la commande {PREFIX}sanctions")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def case(self, ctx, case_id: str):
        await delete_message(ctx)

        case_id = str(int(f"0x{case_id}", 16))

        try:
            split_id = int(case_id[0])
            main_id = int(case_id[1:split_id + 1])
            sanction_type = int(case_id[split_id + 4])
            action_date = int(case_id[split_id + 8:])
            potential_case = await GetDBInfo().info_sanction(main_id)
        except IndexError:
            raise ValueError

        check_1 = SANCTION_TYPE_ID.get(potential_case[0]) == sanction_type

        check_2 = GENID_CREATION + timedelta(seconds=action_date) == datetime.strptime(potential_case[4],
                                                                                       '%Y-%m-%d %H:%M:%S')

        if all([check_1, check_2]):
            embed = await SanctionCommand(self.client).embed_sub_menu(potential_case)
            await ctx.send(embed=embed, delete_after=60)

        else:
            raise ValueError

    @case.error
    async def case_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande case.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help case""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, ValueError):
                await ctx.send(embed=discord.Embed(title='Attention!',
                                                   description=f"L'ID n'existe pas ou a mal été écrit.",
                                                   color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Supprime un dossier à partir de l'ID fournit."
                                  f"Vous pouvez retrouver rapidement la liste des dossiers d'un utilisateur à l'aide "
                                  f"de la commande {PREFIX}sanctions")
    @commands.check_any(check_if_administrator(), check_if_moderator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def delcase(self, ctx, case_id: str):
        await delete_message(ctx)

        case_id = str(int(f"0x{case_id}", 16))

        try:
            split_id = int(case_id[0])
            main_id = int(case_id[1:split_id + 1])
            sanction_type = int(case_id[split_id + 4])
            action_date = int(case_id[split_id + 8:])
            potential_case = await GetDBInfo().info_sanction(main_id)
        except IndexError:
            raise ValueError

        pun_date = datetime.strptime(potential_case[4],'%Y-%m-%d %H:%M:%S')
        check_1 = SANCTION_TYPE_ID.get(potential_case[0]) == sanction_type
        check_2 = GENID_CREATION + timedelta(seconds=action_date) == pun_date

        if all([check_1, check_2]):
            await EditDBPerms().clear_sanction(main_id)
            await ctx.send(
                embed=discord.Embed(title='♻ Le dossier a correctement été effacé',
                                    description=f"La sanction '{potential_case[0].lower()}' appliqué à"
                                                f" <@{potential_case[3]}> le {pun_date.strftime('%d/%m/%Y à %H:%M:%S')}"
                                                f" à été effacé des bases de données.",
                                    color=Infos.default.value), delete_after=60)

        else:
            raise ValueError

    @delcase.error
    async def delcase_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande delcase.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help delcase""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, ValueError):
                await ctx.send(embed=discord.Embed(title='Attention!',
                                                   description=f"L'ID n'existe pas ou a mal été écrit.",
                                                   color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)



def setup(client):
    client.add_cog(Moderation(client))
