from random import randint
from datetime import datetime
import discord
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, victim, before_channel, after_channel, mod=""):
        self.victim = victim
        self.mod = mod
        self.before_channel = before_channel
        self.after_channel = after_channel

    async def _embed_sub_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.victim.id}>", inline=True)
        if self.mod == "":
            embed.add_field(name="🔎 ID joueur:", value=f"{self.victim.id}", inline=True)
        else:
            embed.add_field(name="👤‍ Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
            embed.add_field(inline=True, name="\u200b", value="\u200b")
            embed.add_field(name="🔎 ID joueur:", value=f"{self.victim.id}", inline=True)
            embed.add_field(name="🕵️‍ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.set_thumbnail(url=self.victim.avatar_url)
        embed.add_field(name="🗄 Salon:", value=f"<#{self.before_channel.id}>   **-->**   <#{self.after_channel.id}>",
                        inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def user_switch(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🛫 Changement de salon vocal",
            description=f"{self.victim} a changé de salon vocal.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed

    async def mod_switch(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🛬 Changement forcé de salon vocal",
            description=f"{self.mod} a forcé {self.victim} à changer de salon vocal.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed
