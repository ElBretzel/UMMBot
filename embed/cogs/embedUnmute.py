from datetime import datetime
from utils.checking.clock import get_clock
import discord
import pytz


class EmbedUnmute:
    def __init__(self, member, mod, reason):
        self.member = member
        self.mod = mod
        self.reason = reason

    def duration(self, tz):
        mem_leave = datetime.now(tz)
        mem_join = self.member.joined_at
        mem_join = mem_join.astimezone(tz)
        mem_duration = mem_leave - mem_join

        return mem_duration if mem_duration.days >= 0 else 0

    def member_info(self, embed):
        tz = pytz.timezone('Europe/Paris')

        mem_duration = self.duration(tz)
        clock = datetime.now(tz).strftime(r"%I/%M").split("/")

        embed.set_thumbnail(url=self.member.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.member.id}>", inline=True)
        embed.add_field(name="👤 Pseudo staff:", value=f"<@{self.mod.id}>", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        embed.add_field(name="🕵️ ID staff:", value=f"{self.mod.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name=f"⏲️ Temps passé:", value=f"{mem_duration.days} jours", inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    async def member_unmute(self, color):
        embed = discord.Embed(
            title=f"⚖️ Membre unmute",
            description=f"{self.mod} a unmute {self.member} pour **{self.reason}**",
            colour=color)
        embed = self.member_info(embed)
        return embed
