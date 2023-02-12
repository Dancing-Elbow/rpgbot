import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View

import discordHelper
import helper
import mongoHelper

soldiers = {
    "foot_soldier":
        {
            "cost":
                {
                    "wood": 5,
                    "ore": 5,
                    "gold": 1,
                }
        },
    "archer":
        {
            "cost":
                {
                    "wood": 5,
                    "stone": 5,
                    "gold": 1,
                }
        },
    "horse_man":
        {
            "cost":
                {
                    "stone": 5,
                    "ore": 5,
                    "gold": 1,
                }
        }
}


class Game(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", intents=discord.Intents.all(),
                         activity=discord.Game(name="With DancingElbow"))

        @self.hybrid_command(name="start", description="Start the game!")
        async def start(ctx):
            info = mongoHelper.get_user_info(ctx.author.id)
            embed = discord.Embed(title="Error", description="You already have an account!",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

        @start.error
        async def error(ctx, error):
            if isinstance(error, mongoHelper.NoAccountCreatedError):
                embed = discord.Embed(title="Success!",
                                      description="Successfully created your account. Please see /help to start!",
                                      color=discord.Color.green())
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
                mongoHelper.create_user(ctx.author.id)
                await ctx.send(embed=embed)

        @self.hybrid_command(name="profile", description="See someone's profile!")
        async def profile(ctx, user: discord.Member = None):
            user = user or ctx.author
            information = mongoHelper.get_user_info(user.id)
            embed = discord.Embed(title=f"{user.name} Profile", color=discord.Color.blurple())
            soldiers_message = ""
            for k, v in information["soldiers_inv"].items():
                soldiers_message += k.title().replace("_", " ") + ": " + helper.human_format(v) + "\n"
            embed.add_field(name="Soldiers", value=soldiers_message)
            resources_message = ""
            for k, v in information["resources"].items():
                resources_message += k.title().replace("_", " ") + ": " + helper.human_format(v) + "\n"
            embed.add_field(name="Resources",
                            value=resources_message)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

        @self.hybrid_command(name="inventory", description="See someone's inventory!", aliases=["inv"])
        async def inventory(ctx, user: discord.Member = None):
            user = user or ctx.author
            info = mongoHelper.get_user_info(user.id)
            interaction = View(timeout=60)
            embed1 = discord.Embed(title="Resources", color=discord.Color.blurple())
            for k, v in info["resources_inv"].items():
                message = ""
                for k2, v2 in v.items():
                    message += helper.human_format(int(k2)) + ": " + helper.human_format(int(v2)) + "\n"
                embed1.add_field(name=k.title().replace("_", " "), value=message)
            embed1.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed1, view=interaction)

        @self.hybrid_command(name="daily", description="Get daily loot")
        @commands.cooldown(1, 72000, commands.BucketType.member)
        async def daily(ctx):
            mongoHelper.get_user_info(ctx.author.id)
            mongoHelper.inc_item(ctx.author.id, 1, "resources_inv", "wood", "10000")
            mongoHelper.inc_item(ctx.author.id, 1, "resources_inv", "stone", "10000")
            mongoHelper.inc_item(ctx.author.id, 1, "resources_inv", "ore", "10000")
            mongoHelper.inc_item(ctx.author.id, 1, "resources_inv", "gold", "5000")
            embed = discord.Embed(title="Daily received",
                                  description="Here's what you got:\n1x 10k Wood\n1x 10k Stone\n1x 10k Ore\n1x 5k Gold",
                                  color=discord.Color.green())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

        @self.hybrid_command(name="train", description="Train some soldiers!")
        @app_commands.choices(type=[
            app_commands.Choice(name="Foot Soldier", value="foot_soldier"),
            app_commands.Choice(name="Archer", value="archer"),
            app_commands.Choice(name="Horse Man", value="horse_man"),
        ])
        async def train(ctx, type, amount: discordHelper.numberConverter):
            id = ctx.author.id
            cost = {k: v * amount for k, v in soldiers[type]["cost"].items()}
            await ctx.send(cost)
            canDo = mongoHelper.compare_dict(id, cost, "resources") < 0
            if canDo:
                await ctx.send('you good')
                mongoHelper.inc_item(id, int(amount), "soldiers_inv", type)
                cost = {k: -v for k, v in cost.items()}
                mongoHelper.inc_item_dict(id, cost, "resources")
            else:
                await ctx.send('you poor ass')

        @self.hybrid_command(name="use", description="use an item")
        @app_commands.choices(type=[
            app_commands.Choice(name="Wood", value="wood"),
            app_commands.Choice(name="Stone", value="stone"),
            app_commands.Choice(name="Ore", value="ore"),
            app_commands.Choice(name="Gold", value="gold"),
            app_commands.Choice(name="Crystalized Blood", value="crystalized_blood")
        ])
        async def use(ctx, type, amount: discordHelper.numberConverter):
            id = ctx.author.id
            total_value = sum([int(k) * v for k, v in mongoHelper.get_dict(id, "resources_inv", type).items()])
            await ctx.send("your total value is " + str(total_value))
            used, number = mongoHelper.reach_goal(id, amount, "resources_inv", type)
            if total_value < amount:
                await ctx.send('poor guy literally')
            else:
                await ctx.send("you having enough for the doing")
                mongoHelper.inc_item_dict(id, used, "resources_inv", type)
                mongoHelper.inc_item(id, number, "resources", type)
                await ctx.send(used)

        @self.hybrid_command(name="clear", description="reset data")
        @discordHelper.is_me()
        async def clear(ctx):
            mongoHelper.reset()
            await ctx.send('progress reset')

    async def on_ready(self):
        print(f"Active as {self.user.name} in {len(self.guilds)} server")

    async def setup_hook(self):
        await self.tree.sync()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            embed = discord.Embed(title="Error",
                                  description="You have already used this command. You can use it again in " + helper.seconds_to_time(
                                      error.retry_after) + ".", color=discord.Color.red(),
                                  timestamp=datetime.datetime.now() + datetime.timedelta(seconds=error.retry_after))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRole):
            embed = discord.Embed(title="Error", description="You do not have the roles to use this command.",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        elif isinstance(error, helper.InvalidNumberFormatError):
            embed = discord.Embed(title="Error", description="Invalid number. Please enter a positive number. You can "
                                                             "also use suffixes such as K, M, B, and T to abbreviate "
                                                             "numbers.", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        elif isinstance(error, mongoHelper.NoAccountCreatedError) and ctx.command.name != "start":
            embed = discord.Embed(title="Error",
                                  description="This person has not created an account yet. Start the game with "
                                              "`/start`.",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        else:
            raise error


bot = Game()

bot.run("OTkzNTEzODQ1NTM4NzAxMzI0.GOpyih.MkQL1WV5ZYSSqLutEV_UJUn780aQOsdFpfKkTY")
