import discord
from random import randint
from datetime import datetime
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, user, channel):
        self.user = user
        self.channel = channel

    async def _embed_sub_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        embed.set_thumbnail(url=self.user.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.user.id}>", inline=True)
        embed.add_field(name="🔎 ID joueur:", value=f"{self.user.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name="🗄 Salon:", value=f"<#{self.channel.id}>", inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def voice_disconnect(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"📤 Déconnexion vocale",
            description=f"{self.user} s'est déconnecté d'un salon vocal.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed

    async def voice_connect(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"📥 Connexion vocale",
            description=f"{self.user} s'est connecté à un salon vocal.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self._embed_sub_info(embed)
        return embed
