import asyncio
import discord
import sqlite3

from utils.sql.edit_mute_info import update_mute


async def create_mute_role(guild, role, rolename):
    if rolename in ["mute", "tmute"]:
        perms = [False, True, True, False]
    elif rolename == "vmute":
        perms = [True, False, False, False]
    elif rolename == "gmute":
        perms = [False, False, False, False]
    perms = discord.Permissions(send_messages=perms[0], speak=perms[1], connect=perms[2], change_nickname=perms[3])
    return await guild.create_role(name=role, permissions=perms)


async def match_mutes_perms(guild, role, rolename):
    if rolename == "mute":
        perms = [False, True, True]
    elif rolename == "vmute":
        perms = [True, False, False]
    elif rolename in ["gmute", "tmute"]:
        perms = [False, False, False]
    for channel in guild.channels:
        await channel.set_permissions(role, send_messages=perms[0], speak=perms[1], connect=perms[2])


async def create_mute_role_sql(guild, rolename):
    muted_role = await create_mute_role(guild, rolename.capitalize(), rolename)
    await match_mutes_perms(guild, muted_role, rolename)

    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute(f"""
    UPDATE Role
    SET {rolename} = 1
    WHERE id = ? AND guild_id = ?
    """, (muted_role.id, guild.id))

    connexion.commit()
    connexion.close()

    return muted_role


async def set_punish_mute(guild_id, user_id):
    connexion = sqlite3.connect("database.db")
    cursor = connexion.cursor()

    cursor.execute("""
    SELECT Sanction.id
    FROM Sanction
    INNER JOIN Guild
    ON Sanction.guild_id = Guild.id
    WHERE Guild.id = ? AND Sanction.sanction_user_id = ? AND Sanction.punished = 0 AND 
    (Sanction.sanction_type = 'MUTE' OR Sanction.sanction_type = 'VMUTE' OR Sanction.sanction_type = 'GMUTE')
    """, (guild_id, user_id))

    result = cursor.fetchall()

    connexion.close()

    for i in result:
        await update_mute(i[0])


class TimeMute:

    @staticmethod
    async def mute(member, _time, rolename, *args):

        rolename = rolename.lower()

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        guild = member.guild

        if rolename == 'tmute':
            cursor.execute("""
            SELECT Role.id
            FROM Role
            INNER JOIN Guild
            ON Role.guild_id = Guild.id
            WHERE Guild.id = ? AND tmute = 1
            ;
            """, (guild.id,))
        if rolename == 'mute':
            cursor.execute("""
            SELECT Role.id
            FROM Role
            INNER JOIN Guild
            ON Role.guild_id = Guild.id
            WHERE Guild.id = ? AND mute = 1
            ;
            """, (guild.id,))
        if rolename == 'vmute':
            cursor.execute("""
            SELECT Role.id
            FROM Role
            INNER JOIN Guild
            ON Role.guild_id = Guild.id
            WHERE Guild.id = ? AND vmute = 1
            ;
            """, (guild.id,))
        if rolename == 'gmute':
            cursor.execute("""
            SELECT Role.id
            FROM Role
            INNER JOIN Guild
            ON Role.guild_id = Guild.id
            WHERE Guild.id = ? AND gmute = 1
            ;
            """, (guild.id,))
        role_id = cursor.fetchall()
        connexion.close()

        if not role_id:
            muted_role = await create_mute_role_sql(guild, rolename)

        else:
            muted_role = guild.get_role(role_id[0][0])

        await member.add_roles(muted_role, reason=None)

        if member.voice:
            kick_channel = await member.guild.create_voice_channel("kick")
            await member.move_to(kick_channel)
            await kick_channel.delete()

        if _time > 0:
            await asyncio.sleep(_time)

            try:
                await member.remove_roles(muted_role, reason=None)
            except:
                return

            if args:
                await update_mute(args[0])


class TimeUnmute:

    @staticmethod
    async def unmute(member):

        connexion = sqlite3.connect("database.db")
        cursor = connexion.cursor()

        guild = member.guild

        cursor.execute("""
        SELECT Role.id
        FROM Role
        INNER JOIN Guild
        ON Role.guild_id = Guild.id
        WHERE Guild.id = ? AND (mute = 1 OR vmute = 1 OR gmute = 1)
        ;
        """, (guild.id,))

        role_id = cursor.fetchall()

        if not role_id:
            raise NameError

        else:
            muted_role = [i[0] for i in role_id]

        connexion.close()

        not_mute = True

        for r in member.roles:
            if r.id in muted_role:
                not_mute = False
                await member.remove_roles(guild.get_role(r.id), reason=None)
                await set_punish_mute(guild.id, member.id)

        if not_mute:
            raise NameError


