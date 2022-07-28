from datetime import datetime
from utils.checking.clock import get_clock
import discord
import pytz

from utils.sql.get_db_info import GetDBInfo

from constants import SANCTION_TYPE_ID, GENID_CREATION


class EmbedMute:
    def __init__(self, member, time_, sanction_id):
        self.member = member
        self.time_ = time_
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
        embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name=f"⏲️ Temps passé:", value=f"{mem_duration.days} jours", inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed

    @property
    async def get_sanction_id(self):
        sanction = await GetDBInfo().info_sanction(self.sanction_id)
        return hex(int(f"{len(str(sanction[6]))}{sanction[6]}{str(sanction[7])[::-1][0:3]}{SANCTION_TYPE_ID.get(sanction[0])}{str(sanction[3])[::-1][0:3]}{int((datetime.strptime(sanction[4], '%Y-%m-%d %H:%M:%S')-GENID_CREATION).total_seconds())}")).replace('0x', '')

    async def member_mute(self, color):
        embed = discord.Embed(
            title=f"⚖️ Membre remute | {await self.get_sanction_id}",
            description=f"{self.member} a été remute pendant {self.time_} (leave pendant un mute)",
            colour=color)
        embed = self.member_info(embed)
        return embed

    async def member_vmute(self, color):
        embed = discord.Embed(
            title=f"⚖️ Membre remute | {await self.get_sanction_id}",
            description=f"{self.member} a été remute vocal {self.member} pendant {self.time_} (leave pendant un mute)",
            colour=color)
        embed = self.member_info(embed)
        return embed

    async def member_gmute(self, color):
        embed = discord.Embed(
            title=f"⚖️ Membre remute | {await self.get_sanction_id}",
            description=f"{self.member} a été remute globalement {self.member} pendant {self.time_} (leave pendant un mute)",
            colour=color)
        embed = self.member_info(embed)
        return embed
