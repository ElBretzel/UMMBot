from random import randint
import discord
import pytz
from datetime import datetime, timezone

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, member, detect, state="", mod=""):
        self.member = member
        self.detect = detect
        self.state = state
        self.mod = mod

    def embed_info(self, embed):
        tz = pytz.timezone('Europe/Paris')
        member_creation = self.member.created_at
        member_creation = member_creation.replace(tzinfo=timezone.utc).astimezone(tz)

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.member.id}>", inline=True)
        if self.mod == "":
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        else:
            embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
            embed.add_field(inline=True, name="\u200b", value="\u200b")
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
            embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.set_thumbnail(url=self.member.avatar_url)
        embed.add_field(name="🔎 Création du compte", value=f"{member_creation.strftime('%d/%m/%Y')}",
                        inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)

        return embed

    def member_update_role(self):
        color = [randint(0, 255) for _ in range(3)]
        content = "perdu" if self.state == "d" else "obtenu"
        embed = discord.Embed(
            title=f"🗃️ Membre mis à jour",
            description=f"{self.member} a {content} le rôle <@&{self.detect}>",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.embed_info(embed)
        return embed

    def mod_update_role(self):
        color = [randint(0, 255) for _ in range(3)]
        content = "supprimé" if self.state == "d" else "ajouté"
        embed = discord.Embed(
            title=f"🗃️ Membre mis à jour",
            description=f"{self.mod} a {content} le rôle <@&{self.detect}> à {self.member}",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.embed_info(embed)
        return embed

    def member_update_nick(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗃️ Membre mis à jour",
            description=f"{self.member} a modifié son nickname en **{self.detect}**",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.embed_info(embed)
        return embed

    def mod_update_nick(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗃️ Membre mis à jour",
            description=f"{self.mod} a modifié le nickname de {self.member} en **{self.detect}**",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.embed_info(embed)
        return embed
