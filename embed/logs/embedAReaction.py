from datetime import datetime
from random import randint
import discord
import pytz

from utils.checking.clock import get_clock


class Embed:
    def __init__(self, reaction, user, message):
        self.user = user
        self.message = message
        self.reaction = reaction

    async def reaction_add(self):
        tz = pytz.timezone('Europe/Paris')

        clock = datetime.now(tz).strftime(r"%I/%M").split("/")
        color = [randint(0, 255) for _ in range(3)]
        embed = discord.Embed(
            title=f"📎 Réaction ajoutée",
            description=f"{self.user} a ajouté une réaction au message de {self.message.author}.",
            colour=discord.Colour.from_rgb(color[0], color[1], color[2]))
        embed.set_thumbnail(url=self.user.avatar_url)
        embed.add_field(name="🔎 ID joueur:", value=f"{self.user.id}", inline=True)
        embed.add_field(name="🗄 ID message:", value=f"{self.message.id}", inline=True)
        embed.add_field(name=f"🔗 URL:", value=f"[Clique ici]({self.message.jump_url})", inline=False)
        embed.add_field(name=f"{get_clock(clock)} Heure de l'action:",
                        value=f"{datetime.now(tz).strftime(r'%d/%m/%Y  %H:%M:%S')}", inline=False)
        return embed
