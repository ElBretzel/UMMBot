from utils.checking.clock import get_clock
import discord
import pytz
from datetime import datetime


class EmbedClear:
    def __init__(self, channel, number, mod):
        self.mod = mod
        self.channel = channel
        self.number = number

    async def _embed_sub_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")

        embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
        embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.set_thumbnail(url=self.mod.avatar_url)
        embed.add_field(name="🗄 Salon:", value=f"<#{self.channel.id}>", inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def clear_message(self, color):
        embed = discord.Embed(
            title=f"🔊 Suppression massive",
            description=f"{self.mod} a supprimé **{self.number}** message(s) dans le salon {self.channel}.",
            colour=color)
        embed = await self._embed_sub_info(embed)
        return embed
