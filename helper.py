import math

from discord.ext import commands


class InvalidNumberFormatError(commands.CommandError):
    pass


def seconds_to_time(seconds):
    seconds = -round(-seconds)
    hours = round(seconds / 3600 - .5)
    seconds = seconds % 3600
    minutes = round(seconds / 60 - .5)
    seconds = seconds % 60
    message = ""
    if hours:
        message += f"{hours} hours "
    if minutes:
        message += f"{minutes} minutes "
    if seconds:
        message += f"{seconds} seconds"
    return message


def number_format(str):
    mag = ['', 'K', 'M', 'B', 'T']
    if str.isnumeric():
        num = int(str)
    elif str[:-1].isnumeric():
        if str[-1].upper() in mag:
            num = int(str[:-1]) * math.pow(1000, mag.index(str[-1].upper()))
        else:
            raise InvalidNumberFormatError
    else:
        raise InvalidNumberFormatError
    if num > 0:
        return num
    raise InvalidNumberFormatError


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
