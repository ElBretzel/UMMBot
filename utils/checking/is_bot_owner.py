from discord.ext import commands
from utils.error_handler import ErrorMemberNotBotOwner


def check_if_bot_owner():
    def predicate(ctx):
        if ctx.guild.owner_id == ctx.author.id:
            return True
        else:
            raise ErrorMemberNotBotOwner
    return commands.check(predicate)
