from datetime import datetime
from random import randint
import discord
import pytz

from utils.checking.clock import get_clock

from utils.sql.get_db_info import GetDBInfo

from constants import SANCTION_TYPE_ID, GENID_CREATION


class EmbedBan:
    def __init__(self, member, mod, reason, sanction_id):
        self.member = member
        self.mod = mod
        self.reason = reason
        self.sanction_id = sanction_id

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

    @property
    async def get_sanction_id(self):
        sanction = await GetDBInfo().info_sanction(self.sanction_id)
        return hex(int(
            f"{len(str(sanction[6]))}{sanction[6]}{str(sanction[7])[::-1][0:3]}{SANCTION_TYPE_ID.get(sanction[0])}{str(sanction[3])[::-1][0:3]}{int((datetime.strptime(sanction[4], '%Y-%m-%d %H:%M:%S') - GENID_CREATION).total_seconds())}")).replace(
            '0x', '')

    async def member_ban(self, color):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"⚖️ Membre banni | {await self.get_sanction_id}",
            description=f"{self.mod} a ban {self.member} avec UMMBOT pour **{self.reason}**",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = self.member_info(embed)
        return embed
