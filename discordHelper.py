import discord
from discord import app_commands
from discord.ext import commands

import helper


def is_me():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 715256839356547073

    return app_commands.check(predicate)


class numberConverter(commands.Converter):
    async def convert(self, ctx, argument: str):
        return helper.number_format(argument)
