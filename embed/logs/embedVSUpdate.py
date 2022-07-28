from random import randint
from datetime import datetime
import discord
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, user, channel, state):
        self.user = user
        self.channel = channel
        self.state = state

    async def _embed_sub_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        embed.set_thumbnail(url=self.user.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.user.id}>", inline=True)
        embed.add_field(name="🔎 ID joueur:", value=f"{self.user.id}", inline=True)
        embed.add_field(name="🗄 Salon:", value=f"<#{self.channel.id}>", inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def voice_on(self):
        color = [randint(0, 255) for _ in range(3)]
        content = "muet" if self.state == "UNMUTE" else "sourd"
        embed = discord.Embed(
            title=f"🎙 Changement de statut: {self.state}",
            description=f"{self.user} n'est plus {content}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed

    async def voice_off(self):
        color = [randint(0, 255) for _ in range(3)]
        content = "muet" if self.state == "MUTE" else "sourd"
        embed = discord.Embed(
            title=f"🎙 Changement de statut: {self.state}",
            description=f"{self.user} est devenu {content}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed
