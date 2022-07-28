import asyncio
from discord.errors import NotFound
import sqlite3

from utils.error_handler import ErrorPaginatorCharacter

from constants import BOT_ID

ARROW = {"left": "◀",
         "right": "▶",
         "stop": "❌"}
MAX_EMBED = 1800
MAX_SIZE = 500


async def bot_delete_message(message):
    await message.delete()
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()
    cursor.execute("""
    INSERT INTO Mod_Action ( guild_id, mod_id, user_id, action_, type )
    VALUES ( ?, ?, ?, ?, ? )
    ;     
    """, (message.guild.id, BOT_ID, message.author.id, "DELETE", "BOT"))
    connexion.commit()
    connexion.close()


class Paginator:

    def __init__(self, client, ctx, embed_name, embed_content, embed_index=0, embed_sep="\n", prefix="°",
                 react_message=False):
        self.client = client
        self.ctx = ctx
        self.embed_index = embed_index
        self.embed_content = embed_content
        self.embed_name = embed_name
        self.embed_sep = embed_sep
        self.prefix = prefix
        self.page = 0
        self.index = 0
        self.react_message = react_message

        self.result = None

    @property
    def content_builder(self):

        if self.prefix != "number":
            return [f"{self.prefix} {i}" for i in self.embed_content]

        n_page = len(self.embed_content) // 10
        n_page += 1 if len(self.embed_content) % 10 >= 1 else 0

        li = []
        current_index = 0

        for _ in range(n_page):
            for n in range(1, 11):
                li.append(f"__{n}__ " + f"**{self.embed_content[current_index]}**")
                current_index += 1

                if current_index == len(self.embed_content):
                    return li

    async def paginator_wait_for(self, message, reactions, member_id, time=60.0):
        def check_reaction(reaction, user):
            return (reaction.message.id == message.id and
                    str(reaction.emoji) in reactions.values() and user.id == member_id)

        def check_message(m):
            return m.channel.id == message.channel.id and self.ctx.author.id == m.author.id

        if self.react_message:
            pending_tasks = [self.client.wait_for('message', check=check_message),
                             self.client.wait_for('reaction_add', timeout=time, check=check_reaction)]

            done_task, pending_task = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
            return done_task, pending_task
        else:
            pending_tasks = [self.client.wait_for('reaction_add', timeout=time, check=check_reaction)]
            done_task, pending_task = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
            return done_task, pending_task
    @property
    def set_index_value(self):

        return f'{self.embed_sep}'.join(self.embed_content[self.page])

    async def paginator_check_input(self, message, embed, max_page):

        await message.clear_reactions()

        if self.page == 0 and max_page > 0:
            await message.add_reaction(ARROW["right"])

        elif self.page == max_page and max_page > 0:
            await message.add_reaction(ARROW["left"])

        elif max_page > 0:
            await message.add_reaction(ARROW["left"])
            await message.add_reaction(ARROW["right"])
        await message.add_reaction(ARROW["stop"])

        done_task, pending_task = await self.paginator_wait_for(message, ARROW, self.ctx.author.id)

        if pending_task:
            for p_task in pending_task:
                p_task.cancel()

        for d_task in done_task:

            try:
                task_result = d_task.result()
            except asyncio.TimeoutError:
                try:
                    await message.delete()
                    return
                except NotFound:
                    return

        if isinstance(task_result, tuple):

            react = str(task_result[0].emoji)
            if react == ARROW["left"]:
                self.page -= 1

            elif react == ARROW["right"]:
                self.page += 1

            elif react == ARROW["stop"]:
                await message.delete()
                return

            embed.set_field_at(self.embed_index, name=self.embed_name, value=self.set_index_value)
            embed.set_footer(text=f"Page {int(self.page) + 1} / {int(max_page) + 1}")
            await message.edit(embed=embed)
        else:
            msg = task_result
            await bot_delete_message(msg)
            if msg.content in [str(i) for i in range(1, 11)]:
                self.index = int(msg.content)
                index = int(msg.content)
                content_page = self.embed_content[self.page]
                if len(content_page) >= index:
                    content = content_page[index - 1]
                    content = content.split("**")[1]

                    try:
                        await message.delete()
                    except NotFound:
                        return
                    self.result = content
                    return
        await self.paginator_check_input(message, embed, max_page)

    async def paginator_create(self, channel, embed):

        list_of_content = []
        len_group = previous_index = max_page = 0

        content = self.content_builder

        if not content:
            return

        seperate_group = False
        if self.embed_sep == "\n":
            seperate_group = True

        for index, item in enumerate(content):

            len_group += len(item)
            len_current = len(item)

            if len_current >= MAX_EMBED:
                raise ErrorPaginatorCharacter

            if (len_group > MAX_SIZE and not seperate_group) or (seperate_group and index % 10 == 0):

                new_content = content[previous_index:index]
                if new_content:
                    max_page += 1
                    list_of_content.append(new_content)

                previous_index = index
                len_group = len_current

        list_of_content.append(content[previous_index:])
        self.embed_content = list_of_content

        self.page = 0
        embed.set_field_at(self.embed_index, name=self.embed_name, value=self.set_index_value)
        embed.set_footer(text=f"Page {int(self.page) + 1} / {int(max_page) + 1}")
        message = await channel.send(embed=embed, delete_after=60)

        await self.paginator_check_input(message, embed, max_page)