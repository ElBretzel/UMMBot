from datetime import datetime
from random import randint
import discord
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, member, channel, message, mod=""):
        self.member = member
        self.mod = mod
        self.channel = channel
        self.message = message

    async def _embed_sub_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")

        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.member.id}>", inline=True)
        if self.mod == "":
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        else:
            embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
            embed.add_field(inline=True, name="\u200b", value="\u200b")
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
            embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.set_thumbnail(url=self.member.avatar_url)

        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name="📋 Contenu du message:", value=f"{self.message.content[0:500]}", inline=False)
        embed.add_field(name="🗄 Salon:", value=f"<#{self.channel.id}>", inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def user_delete(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗑 Message supprimé",
            description=f"{self.member} a supprimé son message.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed

    async def mod_delete(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🔊 Message supprimé",
            description=f"{self.mod} a supprimé le message de {self.member}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed
