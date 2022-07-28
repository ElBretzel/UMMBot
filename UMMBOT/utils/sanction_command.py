import discord
import asyncio
from discord.ext import commands
import pytz
from datetime import datetime
import textwrap

from utils.paginator import Paginator

from constants import Infos, OWNER, SANCTION_REACTION_MAIN, SANCTION_TYPE_ID, GENID_CREATION

tz = pytz.timezone('Europe/Paris')
clock = datetime.now(tz).strftime(r"%I/%M").split("/")

sub_reaction = ("◀", SANCTION_REACTION_MAIN.get("cancel"))


class ConvertUser(commands.UserConverter):
    async def convert(self, ctx, arg):
        user = await super().convert(ctx, arg)
        return user


async def send_message(ctx, embed):
    await ctx.send(embed=embed)


async def edit_message(embed, previous_message):
    await previous_message.edit(embed=embed)
    await previous_message.clear_reactions()


async def clear_message(message):
    try:
        await message.delete()
    except:
        return


class SanctionCommand:

    def __init__(self, client):
        self.client = client

    async def wait_main_reaction(self, ctx, message, user, sanctions):

        reaction_used = []

        for k, v in SANCTION_REACTION_MAIN.items():
            if sanctions.get(k):
                if sanctions.get(k)[0] < 1:
                    continue
            await message.add_reaction(v)
            reaction_used.append(v)

        def check_reaction(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(
                reaction.emoji) in reaction_used

        try:
            react, _ = await self.client.wait_for('reaction_add', timeout=60.0,
                                                  check=check_reaction)
        except asyncio.TimeoutError:
            await clear_message(message)
            return
        await clear_message(message)

        react = str(react.emoji)

        if react in SANCTION_REACTION_MAIN.get("cancel"):
            return
        else:

            for k, v in SANCTION_REACTION_MAIN.items():
                if v == react:
                    sanction = sanctions.get(k)

            await self.setup_paginator(ctx, user, sanction, sanctions)

    async def setup_paginator(self, ctx, user, sanction, sanctions):

        embed = await self.embed_paginator_menu(sanction, user)

        paginator = Paginator(self.client, ctx,
                                          f"Veillez écrire le chiffre correspondant au dossier que vous souhaitez consulter.",
                                          [f"{i[0]} - {textwrap.shorten(i[1], width=95, placeholder='...')}"
                                           for i in sanction[1]], prefix="number", react_message=True)

        await paginator.paginator_create(ctx.channel, embed)

        if not paginator.result:
            embed = await self.embed_main_menu(ctx, user, sanctions)
            message = await ctx.send(embed=embed, delete_after=60)
            await self.wait_main_reaction(ctx, message, user, sanctions)
            return

        await self.wait_sub_reaction(ctx, paginator, user, sanction, sanctions)

    async def wait_sub_reaction(self, ctx, paginator, user, sanction, sanctions):

        def check_reaction(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(
                reaction.emoji) in sub_reaction

        embed = await self.embed_sub_menu(sanction[1][(paginator.page * 10 + paginator.index) - 1])
        message = await ctx.send(embed=embed, delete_after=60)

        for r in sub_reaction:
            await message.add_reaction(r)

        try:
            react, _ = await self.client.wait_for('reaction_add', timeout=60.0,
                                                  check=check_reaction)
        except asyncio.TimeoutError:
            await clear_message(message)
            return
        await clear_message(message)

        react = str(react.emoji)

        if react in SANCTION_REACTION_MAIN.get("cancel"):
            embed = await self.embed_main_menu(ctx, user, sanctions)
            message = await ctx.send(embed=embed, delete_after=60)
            await self.wait_main_reaction(ctx, message, user, sanctions)
            return
        else:
            await self.setup_paginator(ctx, user, sanction, sanctions)
            return

    async def embed_paginator_menu(self, sanction, user):
        embed = discord.Embed(title=f"⚖️Dossier de {sanction[1][0][0].lower()} de {user.name}",
                              description=f"{user} a **{sanction[0]}** cas de {sanction[1][0][0].lower()}",
                              color=Infos.default.value)
        embed.add_field(name=".", value=".")

        return embed

    async def embed_sub_menu(self, sanction):

        sanction_id = f"{len(str(sanction[6]))}{sanction[6]}{str(sanction[7])[::-1][0:3]}{SANCTION_TYPE_ID.get(sanction[0])}{str(sanction[3])[::-1][0:3]}{int((datetime.strptime(sanction[4], '%Y-%m-%d %H:%M:%S') - GENID_CREATION).total_seconds())}"

        embed = discord.Embed(title=f"🔎 Information sur le casier n°{sanction[6]}",
                              description=f"**ID de la sanction**: {hex(int(sanction_id)).replace('0x', '')}",
                              color=Infos.success.value)

        embed.add_field(name="Type d'effraction:", value=f"{sanction[0]}")
        embed.add_field(name="Description donnée:",
                        value=f"{textwrap.shorten(sanction[1], width=500, placeholder='...')}")
        mod_user = await self.client.fetch_user(sanction[2])
        member_user = await self.client.fetch_user(sanction[3])
        embed.add_field(name="Modérateur:", value=f"<@{mod_user.id}>")
        embed.add_field(name="Membre:", value=f"<@{member_user.id}>")
        embed.add_field(name="Crée le:", value=f"{sanction[4]}")
        if sanction[0] in ["VMUTE", "GMUTE", "MUTE"]:
            print(sanction)
            embed.add_field(name="Termine le:", value=f"{sanction[8]}")
        embed.add_field(name="Etat:", value=f"{'Traité' if sanction[5] else 'Non traité'}")
        return embed

    async def embed_main_menu(self, ctx, user, sanctions):

        embed = discord.Embed(
            title=f"⚖️ Sanctions de {user}",
            description=f"Pour plus d'information sur le casier, veillez cliquer sur les différentes réactions",
            colour=Infos.default.value)
        embed.set_author(name=f"{ctx.author}", icon_url=f"{ctx.guild.icon_url}")
        embed.set_footer(
            text=f"Bot custom du serveur {ctx.guild}. Pour plus d'information, veillez contacter {OWNER}",
            icon_url=self.client.user.avatar_url)
        embed.add_field(name="💣 Warn:", value=f"{sanctions.get('WARN')[0]}", inline=True)
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="🎙 Mute:", value=f"{sanctions.get('MUTE')[0]}", inline=True)
        embed.add_field(name="⏳ Kick:", value=f"{sanctions.get('KICK')[0]}", inline=True)
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="🔨 Ban:", value=f"{sanctions.get('BAN')[0]}", inline=True)

        return embed
