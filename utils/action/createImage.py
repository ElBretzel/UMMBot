import discord
from io import BytesIO
from PIL import Image
import requests
from os import path

class customImage:
    def __init__(self, client, id_rand):
        self.client = client
        self.channel = client.get_channel(697197422111227946)
        self.id_rand = id_rand

    async def publish_image(self):
        img_file = discord.File(f"image_{self.id_rand}.png", filename=f"image_{self.id_rand}.png")
        await self.channel.send(self.id_rand, file=img_file, delete_after=30)

    def create_admin_image(self, avatar, dir_img, image_name):
        response = requests.get(avatar.avatar_)
        bg = Image.open(BytesIO(response.content))
        img = Image.open(path.join(dir_img, image_name)).convert("RGBA")
        img = img.resize(bg.size)
        bg.paste(img, (0, 0), img)
        bg.save(f"image_{self.id_rand}.png", "PNG")





