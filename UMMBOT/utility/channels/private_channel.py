import asyncio
from json import load, dump
from random import sample


def get_channel():
    with open("private_channel_info.json", "r") as f:
        return load(f)


def write_entry(last_dict):
    with open("private_channel_info.json", "w") as f:
        dump(last_dict, f, indent=4)


class PrivateChannel:
    def __init__(self, client, member, before_channel, after_channel):
        self.client = client
        self.member = member
        self.before_channel = before_channel
        self.after_channel = after_channel

    async def voice_connect(self):
        get_chan = get_channel()
        for g in get_chan:
            if g.get("guild") == self.member.guild_.id:
                gen = g["gen"]
                break
        else:
            get_chan.append(
                {
                    "guild": self.member.guild_.id,
                    "gen": "?",
                    "category": "?",
                }
            )
            gen = get_chan[-1]["gen"]
            write_entry(get_chan)

        if self.after_channel.id_ == gen:
            await Voice(self.client, self.member).create_channel()

    async def voice_disconnect(self):
        get_chan = get_channel()
        for id_, g in enumerate(get_chan):
            if g.get("guild") == self.member.guild_.id and g.get("channel"):
                for v in g["channel"]:
                    if v["id_voice"] == self.before_channel.id_:
                        break
                break
        else:
            return

        for num, info in enumerate(g["channel"]):
            if info["owner"] == self.member.name_:
                if len(info["participant"]) == 1:
                    await Voice(self.client, self.member).delete_channel(info["id_voice"], info["id_text"])
                    get_chan[id_]["user"].pop(num)
                    get_chan[id_]["channel"].pop(num)
                else:
                    new_owner = self.member.name_
                    while new_owner == new_owner:
                        new_owner = sample(info["participant"])
        write_entry(get_chan)
        #get_chan[id_]["user"][num]["owner"] == "False

    async def switch_owner(self):
        get_chan = get_channel()


class Voice:
    def __init__(self, client, member):
        self.client = client
        self.member = member  # constant

    async def create_channel(self):

        get_chan = get_channel()
        for id_, g in enumerate(get_chan):
            if g["guild"] == self.member.guild_.id:
                break
        else:
            return

        if not g.get("user"):
            get_chan[id_]["user"] = [{
                "name": self.member.name_,
                "owner": "True",
            }]
        else:
            for v in g["user"]:
                if v["name"] == self.member.name_:
                    return
            else:
                get_chan[id_]["user"].append({
                    "name": self.member.name_,
                    "owner": "True",
                })

        guild = self.member.guild_
        voice_channel_name = f"﹝📞﹞∙Salon⁃de⁃{self.member.name_}"
        text_channel_name = f"﹝📌﹞∙Gestionnaire⁃de⁃salon"
        category_ = self.client.get_channel(g["category"])
        voice_channel = await guild.create_voice_channel(voice_channel_name, category=category_)
        text_channel = await guild.create_text_channel(text_channel_name, category=category_)

        if not g.get("channel"):
            get_chan[id_]["channel"] = [{
                "id_voice": voice_channel.id,
                "id_text": text_channel.id,
                "owner": self.member.name_,
                "participant": [self.member.name_]
            }]
        else:
            get_chan[id_]["channel"].append({
                "id_voice": voice_channel.id,
                "id_text": text_channel.id,
                "owner": self.member.name_,
                "participant": [self.member.name_]
            })

        await voice_channel.set_permissions(self.client.user, connect=True, read_messages=True)
        await voice_channel.set_permissions(self.member.member, connect=True, read_messages=True)
        await voice_channel.set_permissions(guild.default_role, connect=False, read_messages=True)

        await text_channel.set_permissions(self.client.user, read_messages=True)
        await text_channel.set_permissions(self.member.member, read_messages=True)
        await text_channel.set_permissions(guild.default_role, read_messages=False)
        await voice_channel.edit(user_limit=1)
        await asyncio.sleep(1)
        await self.member.member.move_to(voice_channel)
        await text_channel.send(content=f'<@{self.member.id_}>')

        write_entry(get_chan)

    async def delete_channel(self, voice, text):
        voice_channel = self.client.get_channel(voice)
        text_channel = self.client.get_channel(text)

        await voice_channel.delete()
        await text_channel.delete()
