from discord.ext import commands
from utils.ascii_image import Asciimage
from utils.ascii_gif_gen import GenAscii
from utils.ascii_text import Ascii
from utils.gascii import Gascii


class Utilitaire(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def asciify(self, ctx, *hexcode):
        if not ctx.message.attachments:
            await ctx.message.delete()
            return
        await Asciimage(self.client).asciify(ctx, *hexcode)

    @commands.command()
    async def genascii(self, ctx, *args):
        if not ctx.message.attachments:
            await ctx.message.delete()
            return
        await GenAscii(self.client).genascii(ctx, *args)

    @commands.command()
    async def gascii(self, ctx, *args):
        if not ctx.message.attachments:
            await ctx.message.delete()
            return
        await Gascii(self.client).gascii(ctx, *args)

    @commands.command()
    async def ascii(self, ctx, font, *args):
        await ctx.message.delete()
        await Ascii(self.client).ascii(ctx, font, *args)

    @commands.command()
    async def ascii_fonts(self, ctx, *args):
        await ctx.message.delete()
        await Ascii(self.client).ascii_fonts(ctx, *args)


def setup(client):
    client.add_cog(Utilitaire(client))
