from datetime import timedelta
from discord.ext import commands


class ErrorConvertionTime(commands.CheckFailure):
    def __init__(self):
        super().__init__(message="Le format du temps est mal défini")


async def convert_time(arg):
    seconds_in_unit = {"s": 1, "min": 60, "h": 3600, "d": 86400,
                       "w": 604800, "mo": 2628000, "y": 31622400}
    for unit in seconds_in_unit:
        if unit in arg:
            return int(arg.split(unit)[0]) * seconds_in_unit[unit]
    else:
        raise ErrorConvertionTime


async def time_reason(time_duration):
    reason = ""
    time_duration = timedelta(seconds=time_duration)
    days, seconds = time_duration.days, time_duration.seconds

    years = days // 365
    str_years = "années" if years > 1 else "année"

    months = (days % 365) // 30
    weeks = (days % 30) // 7
    str_weeks = "semaines" if weeks > 1 else "semaine"

    days = days % 7
    str_days = "jours" if days > 1 else "jour"

    hours = (days * 24 + seconds // 3600) % 24
    str_hours = "heures" if hours > 1 else "heure"

    minutes = (seconds % 3600) // 60
    str_minutes = "minutes" if minutes > 1 else "minute"

    seconds = seconds % 60
    str_seconds = "secondes" if seconds > 1 else "seconde"

    if years:
        reason += f"{years} {str_years} "
    if months:
        str_months = "mois"

        reason += f"{months} {str_months} "
    if weeks:
        reason += f"{weeks} {str_weeks} "
    if days:
        reason += f"{days} {str_days} "
    if hours:
        reason += f"{hours} {str_hours} "
    if minutes:
        reason += f"{minutes} {str_minutes} "
    if seconds:
        reason += f"{seconds} {str_seconds} "
    return reason
