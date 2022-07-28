from random import randint
import discord
from datetime import datetime, timezone
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, member, before, after):
        self.member = member
        self.before = before
        self.after = after

    async def avatar_update(self):
        tz = pytz.timezone('Europe/Paris')
        member_creation = self.member.created_at
        member_creation = member_creation.replace(tzinfo=timezone.utc).astimezone(tz)

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"🗃️ Utilisateur mis à jour",
            description=f"{str(self.member)} a modifié son avatar.\nAvant: [IMG]({self.before.avatar_url}) Après: [IMG]({self.after.avatar_url})",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed.set_thumbnail(url=self.after.avatar_url)
        embed.add_field(name="🦲 Pseudo joueur:", value=f"<@{self.after.id}>", inline=True)
        embed.add_field(name="🔎 ID joueur:", value=f"{self.after.id}", inline=True)
        embed.add_field(inline=True, name="\u200b", value="\u200b")
        embed.add_field(name="🔎 Création du compte", value=f"{member_creation.strftime('%d/%m/%Y')}",
                        inline=True)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed
