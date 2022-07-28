from utils.error_handler import ErrorMemberLowerRank


async def check_hierarchy(ctx, member):
    guild_owner = ctx.guild.owner_id
    if guild_owner != ctx.author.id or ctx.author.id == member.id:
        top_member = member.top_role
        top_moderator = ctx.author.top_role

        if top_member >= top_moderator or member.id == guild_owner or ctx.author.id == member.id:
            raise ErrorMemberLowerRank
