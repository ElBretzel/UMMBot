from datetime import datetime, timezone
from random import randint
import discord
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, member, mod=""):
        self.member = member
        self.mod = mod

    def duration(self, tz):
        mem_leave = datetime.now(tz)
        mem_join = self.member.joined_at
        mem_join = mem_join.replace(tzinfo=timezone.utc).astimezone(tz)
        mem_duration = mem_leave - mem_join

        return mem_duration if mem_duration.days >= 0 else 0

    def member_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        mem_duration = self.duration(tz)
        clock = datetime.now(tz).strftime(r"%I/%M").split("/")

        embed.set_thumbnail(url=self.member.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.member.id}>", inline=True)
        if self.mod:
            embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
            embed.add_field(inline=True, name="\u200b", value="\u200b")
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
            embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        else:
            embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name=f"⏲️ Temps passé:", value=f"{mem_duration.days} jours", inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def member_leave(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"👋 Membre parti",
            description=f"{self.member} a quitté le serveur.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.member_info(embed)
        return embed

    async def member_kick(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🧹 Membre kick",
            description=f"{self.member} a été kick du serveur par {self.mod.name}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.member_info(embed)
        return embed

    async def member_ban(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"⚖️ Membre banni",
            description=f"{self.member} a été ban du serveur par {self.mod.name}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.member_info(embed)
        return embed
