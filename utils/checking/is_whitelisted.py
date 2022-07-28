from constants import Guild_Info
from utils.error_handler import ErrorGuildNotWhitelisted


def check_if_whitelisted(ctx):

    if ctx.guild is None:
        return False
    elif ctx.guild.id not in Guild_Info.umm_whitelist:
        raise ErrorGuildNotWhitelisted()
    else:
        return True

