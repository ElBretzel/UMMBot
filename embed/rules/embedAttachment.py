import discord
from datetime import datetime
from random import randint
import pytz

from utils.checking.clock import get_clock

from utils.sql.get_db_info import GetDBInfo

from constants import SANCTION_TYPE_ID, GENID_CREATION


class Embed:
    def __init__(self, member, channel, message, file_, detect, sanction_id):
        self.member = member
        self.channel = channel
        self.message = message
        self.file_ = file_
        self.detect = detect
        self.sanction_id = sanction_id

    @property
    async def get_sanction_id(self):
        sanction = await GetDBInfo().info_sanction(self.sanction_id)
        return hex(int(
            f"{len(str(sanction[6]))}{sanction[6]}{str(sanction[7])[::-1][0:3]}{SANCTION_TYPE_ID.get(sanction[0])}{str(sanction[3])[::-1][0:3]}{int((datetime.strptime(sanction[4], '%Y-%m-%d %H:%M:%S') - GENID_CREATION).total_seconds())}")).replace(
            '0x', '')

    async def attachment_embed(self):
        if self.detect == "spoiler":
            embed = await self.attachment_spoiler()
        else:
            embed = await self.attachment_ext()

        return embed

    async def attachment_desc(self, embed):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        content = self.message.content[0:500] if self.message.content else "N/A"
        embed.set_thumbnail(url=self.member.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.member.id}>", inline=True)
        embed.add_field(name="🔎 ID joueur:", value=f"{self.member.id}", inline=True)
        embed.add_field(name="📋 Contenu du message:", value=f"{content[0:500]}", inline=False)
        embed.add_field(name="🗄 Salon:", value=f"<#{self.channel.id}>", inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=True)
        embed.add_field(name=f"🔗 URL:", value=f"[Clique ici]({self.message.jump_url})", inline=True)
        return embed

    async def attachment_spoiler(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗃️ Avertissement membre{'' if not self.sanction_id else ' | ' + str(await self.get_sanction_id)}",
            description=f"""{self.member} a envoyé un fichier sous forme de spoiler\n
*Nom du fichier*: {self.file_.name_}
*Taille du fichier*: {round(self.file_.size_,3)}ko""",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self.attachment_desc(embed)
        return embed

    async def attachment_ext(self):
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗃️ Avertissement membre{'' if not self.sanction_id else ' | ' + str(await self.get_sanction_id)}",
            description=f"""{self.member} a envoyé un fichier avec une extension potentiellement dangereuse: **{self.detect}**\n
*Nom du fichier*: {self.file_.name_}
*Taille du fichier*: {round(self.file_.size_,3)}ko""",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed = await self.attachment_desc(embed)
        return embed
