import asyncio
import discord

from utils.sql.update_db_command import EditDBPerms

from constants import Infos


async def clear_message(message):
    try:
        await message.delete()
    except:
        return


class ClearCommand:
    def __init__(self, client):
        self.client = client

    async def wait_for_reaction(self, ctx, member, type_):

        message = await ctx.send(
            embed=discord.Embed(title='❗ ATTENTION, SUPPRESSION DE DONNEES IMPORTANTES ❗',
                                description=f"Vous venez de demander la suppression de la totalité du dossier de {type_} de <@{member.id}>. "
                                            "En cas de suppression, vous ne pourrez plus récupérer les données supprimées.\n"
                                            "Pour continuer la procédure, cliquez sur la réaction ✅",
                                color=Infos.error.value))

        def check_reaction(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == message.id and str(
                reaction.emoji) in ["✅", "❌"]

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        try:
            react, _ = await self.client.wait_for('reaction_add', timeout=30.0,
                                                  check=check_reaction)
        except asyncio.TimeoutError:
            await clear_message(message)
            return

        await message.clear_reactions()

        react = str(react.emoji)

        if react == "❌":
            await message.edit(
                embed=discord.Embed(title='🩹 Les données ont été conservées',
                                    description=f"Vous avez annulé la requête de suppression de donné de <@{member.id}>.",
                                    color=Infos.default.value), delete_after=10)
        else:

            if type_ == "mute":
                await EditDBPerms().clear_sanctions(ctx, member, "VMUTE")
                await EditDBPerms().clear_sanctions(ctx, member, "GMUTE")
            await EditDBPerms().clear_sanctions(ctx, member, type_.upper())
            await message.edit(
                embed=discord.Embed(title='♻ Les données ont correctement été effacées',
                                    description=f"Le dossier de {type_} de <@{member.id}> a été correctement "
                                                f"effacé des bases de données.",
                                    color=Infos.default.value), delete_after=10)
