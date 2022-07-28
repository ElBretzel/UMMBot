from glob import glob
import pkg_resources
import pyfiglet
import os

from constants import OS_SLASH


class Ascii:
    def __init__(self, client):
        self.client = client

    async def ascii(self, ctx, font, *text):
        try:
            f = pyfiglet.Figlet(font=font)
        except pyfiglet.FontNotFound:
            return
        r = f.renderText(" ".join(text))
        if len(r) > 2000:
            await ctx.send("Message trop long...", delete_after=5)
            return
        await ctx.send(f"```{r}```")

    async def ascii_fonts(self, ctx, *font):
        if font:
            return
        channel = await ctx.author.create_dm()

        location = pkg_resources.resource_filename('pyfiglet', 'fonts')
        fonts = [os.path.splitext(i.split(OS_SLASH)[-1])[0] for i in glob(f"{location}/**.flf")]

        hold = 0
        messages = 0
        for j in fonts:
            hold += len(j)
            if hold > 1500:
                messages += 1
                hold = 0

        for i in range(messages + 1):
            try:
                await channel.send(
                    f"**MESSAGE {i + 1}/{messages + 1}**```{' | '.join(fonts[i * 100:i * 100 + 100])}```")
            except:
                pass
