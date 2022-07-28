import re
import asyncio

import discord
from discord import Embed
from discord.ext import commands

from constants import PREFIX, LOGS, RULES, OWNER, Infos, CHANNEL_LOG
from utils.action.delete_message import delete_message
from utils.checking.is_administrator import check_if_administrator
from utils.checking.is_bot_owner import check_if_bot_owner
from utils.checking.is_whitelisted import check_if_whitelisted
from utils.error_handler import ErrorTooMuchArguments, ErrorUnknownAliase, \
    ErrorGuildNotWhitelisted, ErrorAlreadyExist, ErrorDontExist, ErrorPaginatorCharacter, ErrorIncorrectForm, \
    ErrorMissingArgument
from utils.paginator import Paginator
from utils.sql.get_db_info import GetDBInfo
from utils.sql.update_db_command import EditDBPerms

from utils.clear_sanctions_command import ClearCommand
from utils.rule_panel_command import RulePanel

ALIASES = {"allow": ["allow", "1", "a"],
           "deny": ["deny", "0", "d"],
           "info": ["information", "info", "i"],
           "add": ["add", "1", "a"],
           "remove": ["remove", "0", "r", "d"],
           "whitelist": ["whitelist", "w", "1"],
           "blacklist": ["blacklist", "b", "0"]}

AUTHORIZATION = ["⛔", "✅", "❌"]


class ConvertMember(commands.MemberConverter):
    async def convert(self, ctx, arg):
        member = await super().convert(ctx, arg)
        return member


class ConvertRole(commands.RoleConverter):
    async def convert(self, ctx, arg):
        role = await super().convert(ctx, arg)
        return role


class ConvertTextChannel(commands.TextChannelConverter):
    async def convert(self, ctx, arg):
        channel = await super().convert(ctx, arg)
        return channel


class Administration(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def send_response_embed(self, send_channel, response, command_name):
        await send_channel.send(
            embed=discord.Embed(title=f'🔎 Information {command_name}',
                                description=f"{response}.",
                                color=Infos.success.value), delete_after=10)

    async def reaction_wait_for(self, message, reactions, member, time=60.0):
        def check(reaction, user):
            return (reaction.message.id == message.id and
                    str(reaction.emoji) in reactions and user.id == member.id)

        react, user = await self.client.wait_for('reaction_add', timeout=time, check=check)
        return str(react.emoji)

    # admin_role add/remove/info *role
    # animation_role add/remove/info *role

    @commands.command(aliases=['logs_channel'],
                      description="Permet de configurer ou d'afficher les informations des salons de log.\n"
                                  "Si vous voulez ajouter un salon de log, mettez en argument 'add', "
                                  "pour supprimer un salon de log, mettez 'remove' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def log_channel(self, ctx, option: str, *channel: ConvertTextChannel):

        await delete_message(ctx)

        access = 1 if option.lower() in ALIASES["add"] else 0 if option.lower() in ALIASES[
            "remove"] else "info" if option.lower() in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        channels = await GetDBInfo().info_logchannel(ctx)

        if access == "info":
            channels = [f"\t**<#{g}>**: {l}" for g, l in channels] if channels else ["**Aucun salon paramétré...**"]
            paginator = Paginator(self.client, ctx, "📋 Liste des salons de log:", channels, 0, "\n")

            embed = discord.Embed(
                title="🔭 Informations des salons de log",
                description=f"Pour plus d'information sur cette commande, veillez écrire {PREFIX}help log_channel",
                colour=Infos.default.value)
            embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
            embed.set_footer(
                text=f"Bot custom du serveur {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                icon_url=self.client.user.avatar_url)
            embed.add_field(name=".", value=".")
            await paginator.paginator_create(ctx.channel, embed)
        else:

            channel = ctx.channel if not channel else channel[0]

            show_log = [l for c, l in zip([j[0] for j in channels], CHANNEL_LOG.values()) if c != channel.id and c] \
                if access else \
                [l for c, l in zip([j[0] for j in channels], CHANNEL_LOG.values()) if c == channel.id and c]

            if not show_log:
                show_log = ["Rien à modifier ici..."]

            paginator = Paginator(self.client, ctx,
                                  f"♦️ A quel type de log voulez-vous {'assigner' if access else 'désassigner'} ce salon ?",
                                  show_log, prefix="number", react_message=True)

            embed = Embed(title=f"⚙️ Paramétrage du salon {channel}",
                          description=f"Veillez écrire le chiffre correspondant au log que vous souhaitez assigner.",
                          color=Infos.default.value)
            embed.add_field(name=".", value=".")
            await paginator.paginator_create(ctx.channel, embed)
            logs_type = paginator.result

            if not logs_type:
                return

            for k, v in CHANNEL_LOG.items():
                if v == logs_type:
                    logs_type = k
                    break
            else:
                return

            response = await EditDBPerms().set_logs_channel(access, logs_type, channel, ctx)

            old_channel_response = response.get("old_text")
            new_channel_response = response.get("new_text")

            if response.get("old") and new_channel_response:
                await self.send_response_embed(response["old"], old_channel_response, "des salons log")
                await self.send_response_embed(channel, new_channel_response, "des salons log")
            elif new_channel_response:
                await self.send_response_embed(channel, new_channel_response, "des salons log")
            elif old_channel_response:
                await self.send_response_embed(response["old"], old_channel_response, "des salons log")

    @log_channel.error
    async def log_channel_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande log_channel.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help log_channel""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id du salon spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help log_channel""",
                                    color=Infos.warning.value), delete_after=5)

        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (allow/deny/info).
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help log_channel""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Permet de configurer ou d'afficher les informations des modules de "
                                  "l'automodérateur.\n "
                                  "Si vous voulez autoriser ce module, mettez dans l'argument option 'allow', "
                                  "pour désactiver ce module, mettez 'deny' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def automod(self, ctx, option: str):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["allow"] else 0 if option in ALIASES[
            "deny"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        info_automod = await GetDBInfo().info_automoderation(ctx)

        if access == "info":
            info_automod = [f"**{i}**: {'Activé' if bool(info_automod[n]) else 'Désactivé'}" for n, i in
                            enumerate(RULES.values())]

            embed = discord.Embed(
                title="🔭 Informations de l'automodérateur",
                description=f"Pour plus d'information sur l'automodérateur, veillez écrire {PREFIX}help automod ou {PREFIX}help rules_panel",
                colour=Infos.default.value)
            embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
            embed.set_footer(
                text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                icon_url=self.client.user.avatar_url)
            embed.add_field(name=".", value=".")
            paginator = Paginator(self.client, ctx, "🔎 Statut des modules de l'automodérateur", info_automod, 0, "\n")
            await paginator.paginator_create(ctx.channel, embed)
            return

        else:
            embed = Embed(title=f"⚙️ Paramétrage de l'automodérateur",
                          description=f"Veillez écrire le chiffre correspondant a la règle que vous souhaitez changer.",
                          color=Infos.default.value)
            embed.add_field(name=".", value=".")

            show_rule = [i for n, i in enumerate(RULES.values()) if not bool(info_automod[n])] if \
                access else [i for n, i in enumerate(RULES.values()) if bool(info_automod[n])]

            if not show_rule:
                show_rule = ["Rien à modifier"]

            paginator = Paginator(self.client, ctx,
                                  f"♦️ Quel module voulez-vous {'activer' if access else 'désactiver'} ?",
                                  show_rule, prefix="number", react_message=True)
            await paginator.paginator_create(ctx.channel, embed)
            rule = paginator.result

            if not rule:
                return

            for k, v in RULES.items():
                if v == rule:
                    rule = k
                    break
            else:
                return

        response = await EditDBPerms().set_automod_perms(access, rule, ctx)
        await self.send_response_embed(ctx.channel, response, "de l'automodérateur")

    @automod.error
    async def automod_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande automod.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help automod""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (allow/deny/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help log_channel""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Permet de configurer ou d'afficher les informations des modules de log.\n"
                                  "Si vous voulez autoriser ce module, mettez dans l'argument option 'allow', "
                                  "pour désactiver ce module, mettez 'deny' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def logging(self, ctx, option: str):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["allow"] else 0 if option in ALIASES[
            "deny"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        info_log = await GetDBInfo().info_logs(ctx)

        if access == "info":
            info_log = [f"**{i}**: {'Activé' if bool(info_log[n]) else 'Désactivé'}" for n, i in
                        enumerate(LOGS.values())]

            embed = discord.Embed(
                title="🔭 Informations des logs",
                description=f"Pour plus d'information sur cette commande, veillez écrire {PREFIX}help logging",
                colour=Infos.default.value)
            embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
            embed.set_footer(
                text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                icon_url=self.client.user.avatar_url)
            embed.add_field(name=".", value=".")

            paginator = Paginator(self.client, ctx, "🔎 Statut des modules de log", info_log, 0, "\n")
            await paginator.paginator_create(ctx.channel, embed)
            return

        else:
            embed = Embed(title=f"⚙️ Paramétrage des logs",
                          description=f"Veillez écrire le chiffre correspondant au log que vous souhaitez changer.",
                          color=Infos.default.value)
            embed.add_field(name=".", value=".")

            show_rule = [i for n, i in enumerate(LOGS.values()) if not bool(info_log[n])] if \
                access else [i for n, i in enumerate(LOGS.values()) if bool(info_log[n])]

            if not show_rule:
                show_rule = ["Rien à modifier"]

            paginator = Paginator(self.client, ctx,
                                  f"♦️ Quel module voulez-vous {'activer' if access else 'désactiver'} ?",
                                  show_rule, prefix="number", react_message=True)
            await paginator.paginator_create(ctx.channel, embed)
            log_type = paginator.result

            if not log_type:
                return
            for k, v in LOGS.items():
                if v == log_type:
                    log_type = k
                    break
            else:
                return

        response = await EditDBPerms().set_logs_perms(access, log_type, ctx)
        await self.send_response_embed(ctx.channel, response, "du système de logging")

    @logging.error
    async def logging_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande logging.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help logging""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (allow/deny/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help logging""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=["badword"],
                      description="Permet de configurer ou d'afficher les informations du module de filtrage des mots interdits.\n"
                                  "Si vous voulez ajouter un mot, mettez dans l'argument option 'add', "
                                  "pour supprimer un mot, mettez 'remove' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def badwords(self, ctx, option: str, *word: str):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["add"] else 0 if option in ALIASES[
            "remove"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        badwords = await GetDBInfo().info_badword(ctx)

        if access == "info":
            if word:
                if word[0] in badwords:
                    await ctx.send(embed=discord.Embed(title='💣 Mot interdit',
                                                       description=f"{word[0].capitalize()} est un mot blacklist du serveur.",
                                                       color=Infos.warning.value), delete_after=3)
                else:
                    await ctx.send(embed=discord.Embed(title='✒️ Mot autorisé',
                                                       description=f"{word[0].capitalize()} est un mot autorisé sur le serveur.",
                                                       color=Infos.success.value), delete_after=3)
            else:
                badwords = [f"**{i}**" for i in badwords]
                embed = discord.Embed(
                    title="🔭 Listes des mots interdits",
                    description=f"Pour plus d'information sur cette commande, veillez écrire {PREFIX}help badwords",
                    colour=Infos.default.value)
                embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
                embed.set_footer(
                    text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                    icon_url=self.client.user.avatar_url)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx, "💣 Liste des mots interdits:", badwords, 0, "\n")
                await paginator.paginator_create(ctx.channel, embed)
            return

        elif not access:
            if word:
                word = word[0]
            else:

                embed = Embed(title=f"⚙️ Paramétrage des mots interdits",
                              description=f"Veillez écrire le chiffre correspondant à l'insulte que vous souhaitez à nouveau autoriser.",
                              color=Infos.default.value)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx,
                                      f"♦️ Quel insulte voulez-vous autoriser ?",
                                      [i for i in badwords], prefix="number", react_message=True)
                await paginator.paginator_create(ctx.channel, embed)
                word = paginator.result

            if not word:
                return

            if len(word) > 1:
                return

            response = await EditDBPerms().delete_badword(ctx, word.lower())
        else:
            if not word:
                raise ErrorMissingArgument
            elif len(word) > 1:
                raise ErrorTooMuchArguments

            word = word[0]

            response = await EditDBPerms().add_badword(ctx, word)

        await self.send_response_embed(ctx.channel, response, "du système d'insulte")

    @badwords.error
    async def badwords_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande badwords.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help badwords """,
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (add/remove/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help badwords""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorAlreadyExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce mot a déjà été blacklist du serveur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorDontExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce mot n'a pas été été blacklist du serveur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, ErrorTooMuchArguments):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Le mot ne doit contenir aucun espace.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMissingArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous n'avez spécifié aucun mot.",
                                               color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=['link'],
                      description="Permet de configurer ou d'afficher les informations du module de filtrage des liens.\n"
                                  "Pour ajouter un lien, mettez dans l'argument option 'add', "
                                  "pour supprimer un lien, mettez 'remove' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def links(self, ctx, option: str, *link: str):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["add"] else 0 if option in ALIASES[
            "remove"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        links = await GetDBInfo().info_links(ctx)

        if link:
            link = re.findall(r"[^www]\B[-a-zA-Z0-9@:%_\+~#=.]{1,256}\.[a-zA-Z0-9()]{1,6}", link[0])
            if not link:
                raise ErrorIncorrectForm
            link = link[0]

        if access == "info":

            if link:
                for l, s in links:
                    if l == link and not int(s):
                        await ctx.send(embed=discord.Embed(title='💣 Lien interdit',
                                                           description=f"{link} est un lien blacklist du serveur.",
                                                           color=Infos.warning.value), delete_after=5)
                        break
                else:
                    await ctx.send(embed=discord.Embed(title='✒️ Lien autorisé',
                                                       description=f"{link} est un lien autorisé sur le serveur.",
                                                       color=Infos.success.value), delete_after=5)
            else:
                if links[0][1]:
                    links = [f"**{l}**: {'autorisé' if int(s) else 'interdit'}" for l, s in links]
                else:
                    links = [f"**{l}**" for l, s in links]
                embed = discord.Embed(
                    title="🔭 Informations des liens",
                    description=f"Pour plus d'information sur cette commande, veillez écrire {PREFIX}help links",
                    colour=Infos.default.value)
                embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
                embed.set_footer(
                    text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                    icon_url=self.client.user.avatar_url)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx, "💣 Liste des liens:", links, 0, "\n")
                await paginator.paginator_create(ctx.channel, embed)
            return

        elif not access:
            if not link:
                embed = Embed(title=f"⚙️ Paramétrage des liens",
                              description=f"Veillez écrire le chiffre correspondant au lien que vous souhaitez à "
                                          f"nouveau autoriser.",
                              color=Infos.default.value)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx,
                                      f"♦️ Quel lien voulez-vous autoriser ?",
                                      [i[0] for i in links], prefix="number", react_message=True)
                await paginator.paginator_create(ctx.channel, embed)
                link = paginator.result

            if not link:
                return

            if len(link.split(" ")) > 1:
                return

            response = await EditDBPerms().delete_link(ctx, link)
        else:
            if not link:
                raise ErrorMissingArgument
            elif len(link.split(" ")) > 1:
                raise ErrorTooMuchArguments

            embed = discord.Embed(title='⚠️ Voulez-vous whitelister ou blacklister ce lien ?',
                                  description=f"Pour interdire l'utilisation du site **{link}** "
                                              "cliquez sur la réaction 🚫, pour l'autoriser cliquez sur la réaction ✅.",
                                  color=Infos.warning.value)
            message = await ctx.send(embed=embed)
            for r in AUTHORIZATION:
                await message.add_reaction(r)

            try:
                react = await self.reaction_wait_for(message, AUTHORIZATION, ctx.author)
            except asyncio.TimeoutError:
                await message.delete()
                return

            state = 1 if react == "✅" else 0 if react == "⛔" else "stop"
            await message.delete()
            if state == "stop":
                return

            response = await EditDBPerms().add_link(ctx, link, state)
        await self.send_response_embed(ctx.channel, response, "du système de lien")

    @links.error
    async def links_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande links.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help links """,
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (add/remove/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help links""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorAlreadyExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce lien a déjà été blacklist/whitelist du serveur, "
                                                           f"veillez d'abord le supprimer.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorDontExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce lien n'a pas été blacklist/whitelist du serveur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, ErrorTooMuchArguments):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Le lien ne doit contenir aucun espace.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMissingArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous n'avez spécifié aucun lien.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorIncorrectForm):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Vous n'avez pas envoyé un lien ou le lien n'est pas correct.",
                                               color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=["mention"],
                      description="Permet de configurer ou d'afficher la liste des membres interdit à mentionner.\n"
                                  "Si vous voulez ajouter un membre, mettez dans l'argument option 'add', "
                                  "pour enlever un membre, mettez 'remove' et pour afficher la liste, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def mentions(self, ctx, option: str, *member: ConvertMember):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["add"] else 0 if option in ALIASES[
            "remove"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        mentions = await GetDBInfo().info_blocked_user(ctx)
        members = ["Vous n'avez paramétré aucune mention bloquée..."] if not mentions else [f"<@{i}>" for i in mentions]

        if access == "info":

            if member:
                if member[0].id in mentions:
                    await ctx.send(embed=discord.Embed(title='🚫 Mention interdite',
                                                       description=f"<@{member[0].id}> a interdit de se faire mentionner.",
                                                       color=Infos.warning.value), delete_after=3)
                else:
                    await ctx.send(embed=discord.Embed(title='✅ Mention autorisé',
                                                       description=f"<@{member[0].id}> peut se faire mentionner.",
                                                       color=Infos.success.value), delete_after=3)
            else:

                embed = discord.Embed(
                    title="🔭 Liste des mentions interdites",
                    description=f"Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mentions",
                    colour=discord.Colour.darker_grey())
                embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
                embed.set_footer(
                    text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                    icon_url=self.client.user.avatar_url)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx, "💣 Liste des mentions interdites:", members, 0, "\n")
                await paginator.paginator_create(ctx.channel, embed)
            return

        elif not access:

            if member:
                member = member[0]

            if not member:
                embed = Embed(title=f"⚙️ Paramétrage des mentions interdites",
                              description=f"Veillez écrire le chiffre correspondant au membre que vous souhaitez de "
                                          f"nouveau autoriser à mentionner.",
                              color=Infos.default.value)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx,
                                      f"♦️ Quel mention voulez-vous autoriser ?",
                                      members, prefix="number", react_message=True)
                await paginator.paginator_create(ctx.channel, embed)

                if paginator.result:
                    member_id = ''.join(re.findall(r"\d", paginator.result))
                    if not member_id:
                        return
                else:
                    return

                member = await self.client.fetch_user(int(member_id))

            response = await EditDBPerms().set_member_mention(ctx, member, access)

        else:

            if not member:
                raise ErrorMissingArgument
            elif len(member) > 1:
                raise ErrorTooMuchArguments
            else:
                response = await EditDBPerms().set_member_mention(ctx, member[0], access)

        await self.send_response_embed(ctx.channel, response, "du système de mention")

    @mentions.error
    async def mentions_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande mentions.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mentions """,
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (add/remove/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mentions""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mentions""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorAlreadyExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce membre a déjà été bloqué du serveur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorDontExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce membre n'a pas été bloqué du serveur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, ErrorTooMuchArguments):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Le nom/id du membre ne doit contenir aucun espace.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMissingArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous n'avez spécifié aucun membre.",
                                               color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=["moderation_role"],
                      description="Permet de configurer ou d'afficher la liste des rôles modérateurs.\n"
                                  "Si vous voulez ajouter un rôle, mettez dans l'argument option 'add', "
                                  "pour enlever un rôle, mettez 'remove' et pour afficher la liste, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def mod_role(self, ctx, option: str, *role: ConvertRole):

        await delete_message(ctx)

        option = option.lower()
        access = 1 if option in ALIASES["add"] else 0 if option in ALIASES[
            "remove"] else "info" if option in ALIASES["info"] else "error"
        if access == "error":
            raise ErrorUnknownAliase

        roles = await GetDBInfo().info_moderation(ctx)
        role_info = ["Vous n'avez paramétré aucun rôle modérateur..."] if not roles else [f"<@&{i}>" for i in roles]

        if access == "info":

            if role:
                if role[0].id in roles:
                    await ctx.send(embed=discord.Embed(title='📯 Role modérateur',
                                                       description=f"<@&{role[0].id}> est un rôle modérateur.",
                                                       color=Infos.success.value), delete_after=3)
                else:
                    await ctx.send(embed=discord.Embed(title='🛑 Role non modérateur',
                                                       description=f"<@&{role[0].id}> n'est pas un rôle modérateur.",
                                                       color=Infos.warning.value), delete_after=3)

            else:

                embed = discord.Embed(
                    title="🔭 Liste des rôles modérateurs",
                    description=f"Pour configurer la liste des rôles modérateurs, veillez écrire {PREFIX}help mod_role",
                    colour=discord.Colour.darker_grey())
                embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
                embed.set_footer(
                    text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                    icon_url=self.client.user.avatar_url)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx, "💣 Liste des rôles modérateurs:", role_info, 0, "\n")
                await paginator.paginator_create(ctx.channel, embed)

            return

        elif not access:

            if role:
                role = role[0]

            if not role:
                embed = Embed(title=f"⚙️ Paramétrage des rôles de modération",
                              description=f"Veillez écrire le chiffre correspondant au rôle que vous souhaitez supprimer "
                                          f"de l'équipe de modération.",
                              color=Infos.default.value)
                embed.add_field(name=".", value=".")

                paginator = Paginator(self.client, ctx,
                                      f"♦️ Quel mention voulez-vous autoriser ?",
                                      role_info, prefix="number", react_message=True)
                await paginator.paginator_create(ctx.channel, embed)
                if paginator.result:
                    role = ''.join(re.findall(r"\d", paginator.result))
                    if not role:
                        return
                else:
                    return

                role = ctx.guild.get_role(int(role))

            response = await EditDBPerms().set_mod_role(ctx, role, access)

        else:

            if not role:
                raise ErrorMissingArgument
            elif len(role) > 1:
                raise ErrorTooMuchArguments
            else:
                response = await EditDBPerms().set_mod_role(ctx, role[0], access)

        await self.send_response_embed(ctx.channel, response, "des rôles de modération")

    @mod_role.error
    async def mod_role_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande mod_role.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mod_role """,
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (add/remove/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mod_role""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"""Le nom ou l'id du rôle spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help mod_role""",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorAlreadyExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce rôle est déjà un rôle modérateur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorDontExist):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Ce rôle n'est pas un rôle modérateur.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        elif isinstance(error, ErrorTooMuchArguments):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Le nom/id du rôle ne doit contenir aucun espace.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMissingArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous n'avez spécifié aucun rôle.",
                                               color=Infos.warning.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(aliases=["channel_setting", "channel_settings", "config_channel"],
                      description="Permet de configurer ou d'afficher les règles des salons textuels.\n"
                                  "Si vous voulez autoriser une règle, mettez dans l'argument option 'allow', "
                                  "pour désactiver une règle, mettez 'deny' et pour afficher les informations, 'info'")
    @commands.check(check_if_whitelisted)
    @commands.check_any(check_if_bot_owner(), check_if_administrator())
    async def channel_config(self, ctx, option: str, *channel: ConvertTextChannel):

        await delete_message(ctx)

        option = option.lower()

        access = 1 if option in ALIASES["allow"] else 0 if option in ALIASES[
            "deny"] else "info" if option in ALIASES["info"] else "error"

        if access == "error":
            raise ErrorUnknownAliase

        channel = ctx.channel if not channel else channel[0]

        info_channel = await GetDBInfo().info_channel(ctx, channel)

        if access == "info":

            embed = discord.Embed(
                title=f"🔭 Informations du salon #{channel}",
                description=f"Pour configurer le salon, veillez écrire {PREFIX}help channel_config",
                colour=discord.Colour.darker_grey())
            embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
            embed.set_footer(
                text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                icon_url=self.client.user.avatar_url)
            embed.add_field(name=".", value=".")

            paginator = Paginator(self.client, ctx, "💣 Information du salon:",
                                  [f"**{i}**: {bool(info_channel[n])}" for n, i in enumerate(RULES.values())], 0, "\n")
            await paginator.paginator_create(ctx.channel, embed)
            return

        else:

            embed = Embed(title=f"⚙️ Paramétrage des logs",
                          description=f"Pour répondre, envoyer le chiffre correspondant à votre choix.",
                          color=Infos.default.value)
            embed.add_field(name=".", value=".")

            show_rule = [i for n, i in enumerate(RULES.values()) if not bool(info_channel[n])] if \
                access else [i for n, i in enumerate(RULES.values()) if bool(info_channel[n])]

            show_rule = show_rule if show_rule else ["Rien à modifier"]

            paginator = Paginator(self.client, ctx,
                                  f"♦️ Quel règle voulez-vous {'activer' if access else 'désactiver'} sur ce salon?",
                                  show_rule, prefix="number", react_message=True)

            await paginator.paginator_create(ctx.channel, embed)

            rule_type = paginator.result

            if not rule_type:
                return

            for k, v in RULES.items():
                if v == rule_type:
                    rule_type = k
            else:
                if rule_type not in RULES:
                    return

        response = await EditDBPerms().set_channel_perms(access, rule_type, ctx, channel.id)
        await self.send_response_embed(ctx.channel, response, "des règles de salon textuel")

    @channel_config.error
    async def channel_config_error(self, ctx, error):

        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande channel_config.
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help channel_config""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorMissingArgument):
            await ctx.send(embed=discord.Embed(title='Attention!',
                                               description=f"Vous n'avez spécifié aucun mot.",
                                               color=Infos.warning.value), delete_after=5)
        elif isinstance(error, ErrorUnknownAliase):
            await ctx.send(
                embed=discord.Embed(title='Erreur!',
                                    description=f"""Vous avez mal spécifié l'option de la commande (allow/deny/info).
                          Pour plus d'information sur cette commande, veillez écrire {PREFIX}help logging""",
                                    color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorGuildNotWhitelisted):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Votre serveur n'est pas whitelisté. Veillez contacter **{OWNER}**.",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, ErrorPaginatorCharacter):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"Nous ne pouvons pas afficher correctement le message ( dépasse la limite des 2000 caractères ).",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(title='Permission manquante!',
                                               description=f"Il vous manque des permissions afin d'executer cette commande.",
                                               color=Infos.permissions.value), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(title='Erreur inconnue!',
                                               description=f"Une erreur inconnue est survenue: **{error}**. Veillez contacter **{OWNER}**.",
                                               color=Infos.unknown.value), delete_after=10)

    @commands.command(description="Supprime la totalité des avertissements du joueur spécifié"
                                  "Attention, vous ne pourrez pas retourner en arrière après avoir effectué la "
                                  "commande.")
    @commands.check_any(check_if_administrator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def clearwarns(self, ctx, member: ConvertMember):

        await delete_message(ctx)
        await ClearCommand(self.client).wait_for_reaction(ctx, member, "warn")

    @clearwarns.error
    async def clearwarns_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande clearwarns.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearwarns""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearwarns""",
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

    @commands.command(description="Supprime la totalité des mute du joueur spécifié"
                                  "Attention, vous ne pourrez pas retourner en arrière après avoir effectué la "
                                  "commande.")
    @commands.check_any(check_if_administrator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def clearmutes(self, ctx, member: ConvertMember):

        await delete_message(ctx)
        await ClearCommand(self.client).wait_for_reaction(ctx, member, "mute")

    @clearmutes.error
    async def clearmutes_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande clearmutes.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearmutes""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearmutes""",
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

    @commands.command(description="Supprime la totalité des kick du joueur spécifié"
                                  "Attention, vous ne pourrez pas retourner en arrière après avoir effectué la "
                                  "commande.")
    @commands.check_any(check_if_administrator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def clearkicks(self, ctx, member: ConvertMember):

        await delete_message(ctx)
        await ClearCommand(self.client).wait_for_reaction(ctx, member, "kick")

    @clearkicks.error
    async def clearkicks_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande clearkicks.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearkicks""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearkicks""",
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

    @commands.command(description="Supprime la totalité des ban du joueur spécifié"
                                  "Attention, vous ne pourrez pas retourner en arrière après avoir effectué la "
                                  "commande.")
    @commands.check_any(check_if_administrator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def clearbans(self, ctx, member: ConvertMember):

        await delete_message(ctx)
        await ClearCommand(self.client).wait_for_reaction(ctx, member, "ban")

    @clearbans.error
    async def clearbans_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(title='Erreur!',
                                               description=f"""Vous avez mal spécifié la commande clearbans.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearbans""",
                                               color=Infos.error.value), delete_after=10)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(title='Attention!',
                                    description=f"""Le nom ou l'id de l'utilisateur spécifié n'existe pas.
                        Pour plus d'information sur cette commande, veillez écrire {PREFIX}help clearbans""",
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

    @commands.command(aliase=["rules_panel"], description="Supprime la totalité des mute du joueur spécifié"
                                  "Attention, vous ne pourrez pas retourner en arrière après avoir effectué la "
                                  "commande.")
    @commands.check_any(check_if_administrator(), check_if_bot_owner())
    @commands.check(check_if_whitelisted)
    async def rule_panel(self, ctx):

        await delete_message(ctx)
        await RulePanel(self.client).setup(ctx)

    @clearbans.error
    async def clearbans_error(self, ctx, error):
        try:
            await delete_message(ctx)
        except:
            pass

        if isinstance(error, ErrorGuildNotWhitelisted):
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


def setup(client):
    client.add_cog(Administration(client))
