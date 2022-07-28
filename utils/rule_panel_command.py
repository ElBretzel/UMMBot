import discord
import asyncio

from constants import Infos, OWNER, RULES, PREFIX, CONFIG_AUTOMOD, RULES_AUTOMOD

from utils.paginator import Paginator

from utils.action.converter import time_reason, convert_time, ErrorConvertionTime

from utils.action.delete_message import delete_message_sql
from utils.sql.get_rules import get_automoderation_rules
from utils.sql.update_db_command import EditDBPerms

EMBED_REACT = {"aide": "💡",
               "info": "📋",
               "config": "🖋",
               "stop": "❌",
               "back": "◀"}

VALIDATION = {"agree": "✅", "remove": "❌"}


async def get_rule_info(ctx, rule):
    infos = list(await get_automoderation_rules(ctx.guild, rule[0]))
    infos[0] = [i for i in infos[0][0]]

    index = [n for n, i in enumerate(infos[1]) if i in ("id", "activate")]
    for t in range(len(index)):
        infos[0].pop(index[t] - t)
        infos[1].pop(index[t] - t)

    return {k: v for v, k in zip(infos[0], infos[1])}


class RulePanel:
    def __init__(self, client):
        self.client = client

    async def panel_wait_for(self, ctx, message, dict_react, time=60.0, message_react=False):

        def check_reaction(reaction, user):
            return (reaction.message.id == message.id and
                    str(reaction.emoji) in dict_react.values() and user.id == ctx.message.author.id)

        def check_message(m):
            return (m.channel.id == message.channel.id and
                    m.author.id == ctx.message.author.id)

        if message_react:
            pending_tasks = [self.client.wait_for('message', check=check_message),
                             self.client.wait_for('reaction_add', timeout=time, check=check_reaction)]
            done_task, pending_task = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

        else:
            pending_tasks = [self.client.wait_for('reaction_add', timeout=time, check=check_reaction)]
            done_task, pending_task = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

        return done_task, pending_task

    async def get_task_result(self, ctx, pending_task, done_task, message):
        if pending_task:
            for p_task in pending_task:
                p_task.cancel()

        for d_task in done_task:
            try:
                task_result = d_task.result()
            except asyncio.TimeoutError:
                await message.delete()
                await self.setup(ctx)

            break
        else:
            return

        return task_result

    async def validation_embed(self, ctx, rule, infos, message):

        await message.clear_reactions()
        await message.add_reaction(VALIDATION["remove"])
        await message.add_reaction(VALIDATION["agree"])

        embed = discord.Embed(
            title=f"🏷 Modification de la règle {rule[1]}",
            description=f"Pour recommencer les modifications, cliquez sur ❌. Pour valider, cliquez sur ✅.",
            colour=Infos.default.value)
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)

        for k, v in infos.items():

            if k in ["timemute", "interval"]:
                v1, v2 = await time_reason(v[0]), await time_reason(v[1])
            elif k in ["use_french_bw", "use_english_bw", "use_custom_bw"]:
                v1, v2 = "Oui" if v[0] else "Non", "Oui" if v[1] else "Non"
            elif k in ["limite", "distance"]:
                v1 = v[0] + 1
                v2 = v[1] + 1
            else:
                v1 = v[0]
                v2 = v[1]

            embed.add_field(name="🔹 " + CONFIG_AUTOMOD.get(k), value=f"✂ {v1} | 🖋 {v2}", inline=False)

        await message.edit(embed=embed)

        done_task, pending_task = await self.panel_wait_for(ctx, message, VALIDATION)
        task_result = await self.get_task_result(ctx, pending_task, done_task, message)

        if task_result:
            react = str(task_result[0].emoji)
            if react == VALIDATION["remove"]:
                await self.loop_edit(ctx, rule, await get_rule_info(ctx, rule), message)
            else:
                await EditDBPerms().update_rule_settings(RULES_AUTOMOD.get(rule[0]),
                                                         {i: j[1] for i, j in infos.items()})
                await self.main_menu(ctx, rule, message)
            return

        await message.delete()
        await self.setup(ctx)

    async def help_panel(self, ctx, rule, message):

        await message.clear_reactions()
        await message.add_reaction(EMBED_REACT["back"])
        await message.add_reaction(EMBED_REACT["stop"])

        embed = discord.Embed(
            title=f"⚙️ Aide de configuration des règles",
            description=f"La configuration se passera en plusieurs étapes, il est **très important** de lire ce message jusqu'au bout au moins une fois.",
            colour=Infos.default.value)
        embed.add_field(name="💡 Aide 1: rentrer les valeurs",
                        value="Cliquez sur la réaction correspondante puis rentrer les valeurs demandés",
                        inline=False)
        embed.add_field(name="💡 Aide 2: type de valeur", value="""**[BOOL]**: rentrez soit 'oui' ou 'non'.
                    **[TIME]**: rentrez une valeur temps **( y,mo,w,d,h,min,s )**.
                    **[STR]** rentrez des caractères alphabétiques.
                    **[INT]** rentrez des caractères numériques""", inline=False)
        embed.add_field(name="💡 Aide 3: type de donnée", value="""**Utilisation d'un dictionnaire** -[BOOL]: Permet d'activer ou non un dictionnaire d'insulte pré-configuré que le bot sera capable de détecter.
                    **Nombre d'avertissements avant mute** - [INT]: Nombre de warn maximum de la règle avant de mute.
                    **Temps de mute** - [TIME]: Temps de mute donné lors du dépassement du nombre maximum de warn.
                    **Limite** - [INT]: Limite de détection autorisée avant de warn (ex: dans les règles 'flood', c'est la limite de mots/emotes/lettres répétés.
                    **Distance** - [INT]: Distance maximum entre deux messages/mots afin que la règle soit détecté.
                    **Intervalle** - [TIME] Interval minimum d'envoie de message en fonction de la distance réglée.""",
                        inline=False)
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        await message.edit(embed=embed)

        done_task, pending_task = await self.panel_wait_for(ctx, message, EMBED_REACT)

        task_result = await self.get_task_result(ctx, pending_task, done_task, message)

        if task_result:
            react = str(task_result[0].emoji)
            if react == EMBED_REACT["back"]:
                await self.main_menu(ctx, rule, message)
                return

        await message.delete()
        await self.setup(ctx)

    async def info_panel(self, ctx, rule, message):

        infos = await get_rule_info(ctx, rule)

        await message.clear_reactions()
        await message.add_reaction(EMBED_REACT["back"])
        await message.add_reaction(EMBED_REACT["stop"])

        embed = discord.Embed(
            title=f"🔎️ Information de la règle {rule[1]}",
            description=f"Pour plus d'information concernant ces options, veillez aller à la page d'aide.",
            colour=Infos.default.value)
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)

        for k, v in infos.items():

            if k in ["timemute", "interval"]:
                v = await time_reason(v)
            elif k in ["use_french_bw", "use_english_bw", "use_custom_bw"]:
                v = "Oui" if v else "Non"
            elif k in ["limite", "distance"]:
                v += 1

            embed.add_field(name="🔹 " + CONFIG_AUTOMOD.get(k), value=v, inline=False)

        await message.edit(embed=embed)
        done_task, pending_task = await self.panel_wait_for(ctx, message, EMBED_REACT)

        task_result = await self.get_task_result(ctx, pending_task, done_task, message)

        if task_result:
            react = str(task_result[0].emoji)
            if react == EMBED_REACT["back"]:
                await self.main_menu(ctx, rule, message)
                return

        await message.delete()
        await self.setup(ctx)

    async def loop_edit(self, ctx, rule, rule_dict, message, stage=0, edit_settings=None):

        if edit_settings is None:
            edit_settings = {}

        await message.clear_reactions()

        if stage == len(rule_dict):
            await self.validation_embed(ctx, rule, edit_settings, message)
            return

        await message.add_reaction(EMBED_REACT["back"])
        await message.add_reaction(EMBED_REACT["stop"])

        current_rule = list(rule_dict.items())[stage]  # Only work on Python 3.7+
        if current_rule[0] == "timemute":
            embed = await self.embed_timemute(ctx, current_rule)
        elif current_rule[0] == "nbefore_mute":
            embed = self.embed_nbefore_mute(ctx, current_rule)
        elif current_rule[0] == "use_french_bw":
            embed = self.embed_use_french_bw(ctx, current_rule)
        elif current_rule[0] == "use_english_bw":
            embed = self.embed_use_english_bw(ctx, current_rule)
        elif current_rule[0] == "use_custom_bw":
            embed = self.embed_use_custom_bw(ctx, current_rule)
        elif current_rule[0] == "limite":
            embed = self.embed_limit(ctx, current_rule)
        elif current_rule[0] == "distance":
            embed = self.embed_distance(ctx, current_rule)
        elif current_rule[0] == "check_msg":
            embed = self.embed_check_msg(ctx, current_rule)
        elif current_rule[0] == "interval":
            embed = await self.embed_interval(ctx, current_rule)

        await message.edit(embed=embed)

        done_task, pending_task = await self.panel_wait_for(ctx, message, EMBED_REACT, message_react=True)
        task_result = await self.get_task_result(ctx, pending_task, done_task, message)

        if task_result:
            if isinstance(task_result, discord.Message):
                delete_message_sql(ctx.guild.id, ctx.author.id)
                await task_result.delete()
                task_result = task_result.content
            else:
                react = str(task_result[0].emoji)
                if stage == 0 or react != EMBED_REACT["back"]:
                    await self.main_menu(ctx, rule, message)
                else:
                    edit_settings.pop(list(rule_dict.items())[stage - 1][0])
                    await self.loop_edit(ctx, rule, rule_dict, message, stage - 1, edit_settings)
                return

            if current_rule[0] in ["nbefore_mute", "limite", "distance", "check_msg"]:
                if task_result.isdigit():
                    task_result = int(task_result)
                    if current_rule[0] in ["limite", "distance"]:
                        task_result -= 1
                else:
                    await self.loop_edit(ctx, rule, rule_dict, message, stage, edit_settings)
                    return

            elif current_rule[0] in ["use_french_bw", "use_english_bw", "use_custom_bw"]:
                if isinstance(task_result, str) and task_result in ["oui", "yes", "1"]:
                    task_result = 1

                elif isinstance(task_result, str) and task_result in ["non", "no", "0"]:
                    task_result = 0
                else:
                    await self.loop_edit(ctx, rule, rule_dict, message, stage, edit_settings)
                    return
            elif current_rule[0] in ["interval", "timemute"]:
                try:
                    task_result = await convert_time(task_result)
                except ErrorConvertionTime:
                    await self.loop_edit(ctx, rule, rule_dict, message, stage, edit_settings)
                    return

            edit_settings[current_rule[0]] = [current_rule[1], task_result]
            await self.loop_edit(ctx, rule, rule_dict, message, stage + 1, edit_settings)
            return

        await self.main_menu(ctx, rule, message)

    async def setup(self, ctx):

        embed = discord.Embed(title=f"⚙️ Paramétrage de l'automodérateur",
                              description=f"Veillez écrire le chiffre correspondant a la règle que vous souhaitez changer.",
                              color=Infos.default.value)
        embed.add_field(name=".", value=".")
        paginator = Paginator(self.client, ctx,
                              f"♦️ Quel module voulez-vous modifier ?",
                              [i for i in RULES.values()], prefix="number", react_message=True)
        await paginator.paginator_create(ctx.channel, embed)

        rule_name = paginator.result

        if not rule_name:
            return

        for k, v in RULES.items():
            if v == rule_name:
                rule = k
                break
        else:
            return

        await self.main_menu(ctx, (rule, rule_name))

    async def main_menu(self, ctx, rule, *message: discord.Message):

        embed = discord.Embed(
            title="⚙ Panneau de configuration",
            description=f"Veillez cliquer sur une réaction pour effectuer une action sur la règle **{rule[1].lower()}**",
            colour=Infos.default.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)

        embed.add_field(name="💡 - Aide", value="\u200b")
        embed.add_field(name="📋 - Information", value="\u200b")
        embed.add_field(name="🖋 - Modification", value="\u200b")

        if message:
            await message[0].edit(embed=embed)
            message = message[0]
        else:
            message = await ctx.send(embed=embed)

        await message.clear_reactions()

        await message.add_reaction(EMBED_REACT["aide"])
        await message.add_reaction(EMBED_REACT["info"])
        await message.add_reaction(EMBED_REACT["config"])

        await message.add_reaction(EMBED_REACT["stop"])

        done_task, pending_task = await self.panel_wait_for(ctx, message, EMBED_REACT)

        task_result = await self.get_task_result(ctx, pending_task, done_task, message)

        if task_result:
            react = str(task_result[0].emoji)
            if react == EMBED_REACT["info"]:
                await self.info_panel(ctx, rule, message)
                return

            elif react == EMBED_REACT["config"]:
                await self.loop_edit(ctx, rule, await get_rule_info(ctx, rule), message)
                return

            elif react == EMBED_REACT["aide"]:
                await self.help_panel(ctx, rule, message)
                return

        await message.delete()
        await self.setup(ctx)

    async def embed_timemute(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 Veillez rentrer une valeur de temps: **(y, mo, w, d, h, min, s).\n"
                        f"🗃 Valeur actuelle: {await time_reason(rule[1])}\n⚠ Type de valeur: [TIME]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_nbefore_mute(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 La valeur rentré correspond au nombre maximum d'avertissement avant de se faire mute."
                        f"\n🗃 Valeur actuelle: {rule[1]}\n⚠ Type de valeur: [INT]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_use_french_bw(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 Utilisation d'un dictionnaire pré-rempli d'insultes Francaises\n"
                        f"🗃 Valeur actuelle: {rule[1]}\n⚠ Type de valeur: [BOOL] (exemple: oui / non)",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_use_english_bw(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 Utilisation d'un dictionnaire pré-rempli d'insultes Anglaise\n"
                        f"🗃 Valeur actuelle: {rule[1]}\n⚠ Type de valeur: [BOOL] (exemple: oui / non)",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_use_custom_bw(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 Utilisation du dictionnaire personnalisé à l'aide de la commande {PREFIX}badwords\n"
                        f"🗃 Valeur actuelle: {rule[1]}\n⚠ Type de valeur: [BOOL] (exemple: oui / non)",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_limit(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 La valeur rentrée correspond au nombre maximum de détection dans le même message avant de recevoir un avertissement.\n"
                        f"🗃 Valeur actuelle: {int(rule[1]) + 1}\n⚠ Type de valeur: [INT]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_distance(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 La valeur rentrée correspond à la distance maximum de détection au sein d'un groupe de messages/mots avant de recevoir un avertissement.\n"
                        f"🗃 Valeur actuelle: {int(rule[1]) + 1}\n⚠ Type de valeur: [INT]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    def embed_check_msg(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 La valeur rentrée correspond au nombre de message provenant d'un utilisateur vérifié par le bot.\n"
                        f"🗃 Valeur actuelle: {rule[1]}\n⚠ Type de valeur: [INT]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed

    async def embed_interval(self, ctx, rule):
        embed = discord.Embed(
            title=f"📝 {CONFIG_AUTOMOD.get(rule[0])}",
            description=f"💡 Veillez rentrer une valeur de temps: **(y, mo, w, d, h, min, s).\n"
                        f"🗃 Valeur actuelle: {await time_reason(rule[1])}\n⚠ Type de valeur: [TIME]",
            colour=Infos.permissions.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur de {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        return embed
