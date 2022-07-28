from datetime import datetime
from utils.checking.clock import get_clock
import discord
import pytz


class EmbedUnban:
    def __init__(self, user, mod, reason):
        self.user = user
        self.mod = mod
        self.reason = reason

    def member_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")

        embed.set_thumbnail(url=self.user.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.user.id}>", inline=True)
        embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name="🔎 ID joueur:", value=f"{self.user.id}", inline=True)
        embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def member_unban(self, color):
        embed = discord.Embed(
            title=f"⚖️ Membre unban",
            description=f"{self.mod} a unban {self.user} avec UMMBOT pour **{self.reason}**",
            colour=color)
        embed = self.member_info(embed)
        return embed
