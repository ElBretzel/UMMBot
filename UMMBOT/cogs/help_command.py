import sqlite3
import discord
from discord.ext import commands
import asyncio

from utils.action.delete_message import delete_message
from constants import PREFIX, BLOCK_EMOTE, HELP_CATEGORY, HELP_REACTION, Infos, OWNER

react_main_help = {**{k: i for k, i in zip(HELP_CATEGORY, HELP_REACTION)}, **{"cancel": "❌"}}
react_cmd_help = {"back": "⬅", "dback": "⏪", "cancel": "❌"}
react_cat_help = {"back": "⬅", "cancel": "❌"}


async def help_sqlite(ctx, type_):
    if ctx.guild.owner.id == ctx.author.id:
        return 1

    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute(f"""
    SELECT Role.id
    FROM Role
    INNER JOIN Guild
    ON Role.guild_id = Guild.id
    WHERE Guild.id = ? AND {type_} = 1
    ;
    """, (ctx.guild.id,))

    result = cursor.fetchall()
    connexion.close()

    if not result:
        return 0
    return 1


async def clear_message(message):
    try:
        await message.delete()
    except:
        return


class HelpCustomError:
    def __init__(self, ctx, client, cog=""):
        self.ctx = ctx
        self.cog = cog
        self.client = client

    @property
    async def too_much_argument(self):
        embed = discord.Embed(title='Erreur!', description="Vous avez rentré trop d'arguments!",
                              color=Infos.error.value)
        embed.set_footer(text=f"Commande rentrée: {PREFIX}help {' '.join(self.cog)}",
                         icon_url=self.client.user.avatar_url)
        await self.ctx.send(embed=embed, delete_after=10)

    @property
    async def command_not_found(self):
        embed = discord.Embed(title='Erreur!', description="Cette commande n'existe pas!",
                              color=Infos.error.value)
        input_ = ' '.join(self.cog) if isinstance(self.cog, list) else self.cog
        embed.set_footer(text=f"Commande rentrée: {PREFIX}help {input_}",
                         icon_url=self.client.user.avatar_url)
        await self.ctx.send(embed=embed, delete_after=10)


class HelpCommand(commands.Cog):
    def __init__(self, client):
        self.client = client

    def search_help_cmd(self, cmd_name):
        for c in self.client.walk_commands():
            if cmd_name in [tu.lower() for tu in c.aliases] or c.name.lower() == cmd_name:

                parent = c.full_parent_name
                if len(c.aliases) > 0:
                    aliases = ' **|** '.join(c.aliases)
                    full_cmd_alias = f"[**{c.name}** | **{aliases}**]"
                    if parent:
                        full_cmd_alias = parent + ' ' + full_cmd_alias
                    alias = full_cmd_alias
                else:
                    alias = c.name if not parent else parent + ' ' + c.name

                description = c.description if c.description else "Non spécifié"

                return f"{PREFIX}{alias} {c.signature}", description

    def search_group_cmd(self, cog):
        com_list = []

        for cogs in self.client.cogs:
            if cog == cogs.lower():
                for com in self.client.get_cog(cogs).get_commands():
                    com_list.append(com.name)
                return com_list

    async def check_reaction(self, message, reaction, ctx, command=""):

        for r in reaction.values():
            await message.add_reaction(r)

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(
                reaction.emoji) in HELP_REACTION

        try:
            react, user = await self.client.wait_for('reaction_add', timeout=60.0,
                                                     check=check)
        except asyncio.TimeoutError:
            await clear_message(message)
            return

        else:
            react = str(react.emoji)
            for k, v in reaction.items():
                if v == react:
                    cog_category = k
                    break
            else:
                return

            if cog_category == "cancel":
                await clear_message(message)
                return

            elif cog_category in ["back", "dback"]:
                if cog_category == "back" and command:
                    cog_category = command.cog.qualified_name.lower()
                    embed = await self.help_cat(ctx, cog_category)
                    react = dict(react_cat_help)

                else:
                    embed, perms = await self.help_list(ctx)
                    react = dict(react_main_help)
                    for k, v in perms.items():
                        if not v:
                            react.pop(k, None)

            else:
                if cog_category not in HELP_CATEGORY:
                    embed = await self.help_cmd(ctx, cog_category)
                    react = dict(react_cmd_help)
                else:
                    embed = await self.help_cat(ctx, cog_category)
                    react = dict(react_cat_help)
            await message.edit(embed=embed)
            await message.clear_reactions()
            await self.check_reaction(message, react, ctx)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, ctx, *cog):

        await delete_message(ctx)

        if not cog:
            embed, perms = await self.help_list(ctx)
            react = dict(react_main_help)
            for k, v in perms.items():
                if not v:
                    react.pop(k, None)

            message = await ctx.send(embed=embed)

        else:
            if len(cog) > 1:
                await HelpCustomError(ctx, self.client, cog).too_much_argument
                return

            cog = cog[0].lower()
            for k, v in HELP_CATEGORY.items():
                if cog in v:
                    cog = k
                    break

            if cog not in HELP_CATEGORY:

                command = self.client.get_command(cog)
                if not command:
                    await HelpCustomError(ctx, self.client, cog).command_not_found
                    return

                embed = await self.help_cmd(ctx, cog)
                message = await ctx.send(embed=embed)
                react = dict(react_cmd_help)
                await self.check_reaction(message, react, ctx, command)
                return

            else:
                embed = await self.help_cat(ctx, cog)
                message = await ctx.send(embed=embed)
                react = dict(react_cat_help)

        await self.check_reaction(message, react, ctx)

    @help.error
    async def help_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title='Attention!', description="Cette commande est en cooldown!",
                                  color=Infos.warning.value)
            await ctx.send(embed=embed, delete_after=30)
        else:
            embed = discord.Embed(title='Erreur inconnue!',
                                  description=f"Une erreur inconnue est survenue: **{error}**."
                                              f" Veillez contacter **{OWNER}**.",
                                  color=Infos.unknown.value)
            await ctx.send(embed=embed)

    async def help_list(self, ctx):

        help_perms = {k: False for k in HELP_CATEGORY}

        is_bot_owner = await self.client.is_owner(ctx.author)

        embed = discord.Embed(
            title="📚 Commande d'aide",
            description=f"Le prefixe du bot est **`{PREFIX}`**."
                        f" Pour plus d'information sur certaines catégories, écrivez\n> {PREFIX}help *<catégorie>*",
            colour=discord.Colour.darker_grey())
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(text=f"Bot custom du serveur {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
                         icon_url=self.client.user.avatar_url)

        admin_roles = await help_sqlite(ctx, "admin")
        moderation_roles = await help_sqlite(ctx, "moderation")
        animation_roles = await help_sqlite(ctx, "animation")
        content = _ = BLOCK_EMOTE + " Indisponible"

        mod_roles = {"developpement": is_bot_owner, "administration": admin_roles,
                     "moderation": moderation_roles, "animation": animation_roles}

        if mod_roles["developpement"]:
            content = f"{PREFIX}*help dev*"
            help_perms["developpement"] = True

        embed.add_field(name=" 🚧 Developpement", value=f"{content}", inline=True)

        content = _
        if mod_roles["administration"]:
            content = f"{PREFIX}*help admin*"
            help_perms["administration"] = True

        embed.add_field(name=" 📯 Administration", value=f"{content}", inline=True)

        content = _
        if mod_roles["moderation"]:
            content = f"{PREFIX}*help mod*"
            help_perms["moderation"] = True

        embed.add_field(name="⚖️ Moderation", value=f"{content}", inline=True)

        content = _
        if mod_roles["animation"]:
            content = f"{PREFIX}*help anim*"
            help_perms["animation"] = True

        embed.add_field(name="🎏 Animation", value=f"{content}", inline=True)

        embed.add_field(name=" 💎 Utilitaire", value=f"{PREFIX}*help utilitaire*", inline=True)
        help_perms["utilitaire"] = True
        embed.add_field(name=" 🥁 Musique", value=f"{PREFIX}*help musique*", inline=True)
        help_perms["musique"] = True
        embed.add_field(name=" 🎭 Fun", value=f"{PREFIX}*help fun*", inline=True)
        help_perms["fun"] = True

        return embed, help_perms

    async def help_cmd(self, ctx, cog):
        help_cmd = self.search_help_cmd(cog)

        embed = discord.Embed(
            title=f"📚 Infos commande: {cog}",
            description=f"Description de la commande: **{help_cmd[1]}.**",
            color=Infos.default.value
        )
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        embed.add_field(name="Syntaxe de la commande", value=f"{help_cmd[0]}", inline=True)
        return embed

    async def help_cat(self, ctx, cog):
        com_list = self.search_group_cmd(cog) or ["Bientôt disponible"]

        embed = discord.Embed(
            title=f"📚 Infos catégorie: {cog.capitalize()}",
            description=f"Cette catégorie comporte {len(com_list)} commande{'s' if len(com_list) > 1 else ''}. "
                        f"Pour plus d'information sur certaines commandes, écrivez\n> {PREFIX}help *<commande>*",
            color=Infos.default.value
        )
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        embed.add_field(name="Liste des commandes", value=f"`{', '.join(com_list)}`", inline=True)

        return embed


def setup(client):
    client.add_cog(HelpCommand(client))
