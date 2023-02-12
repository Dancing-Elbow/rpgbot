import collections
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, button, Button
from discord.interactions import Interaction
import pymongo
import datetime

client = pymongo.MongoClient("mongodb+srv://DancingElbow:Sf4VzIuF56QmGTtb@allen.zm335vc.mongodb.net/?retryWrites"
                             "=true&w=majority")
database = client['information']
player_info = database['test']
soldier_time_info = database['soldier_time']
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


class NoAccountCreatedError(commands.CommandError):
    pass


class InvalidNumberFormatError(commands.CommandError):
    pass


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def number_format(str):
    mag = ['', 'K', 'M', 'B', 'T']
    if str.isnumeric():
        num = int(str)
    elif str[:-1].isnumeric():
        if str[-1].upper() in mag:
            num = str[:-1] * mag.index(str[-1].upper())
        else:
            raise InvalidNumberFormatError
    else:
        raise InvalidNumberFormatError
    if num > 0:
        return num
    raise InvalidNumberFormatError


def is_me():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 715256839356547073

    return app_commands.check(predicate)


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


def get_use_resource_items(id, type, goal):
    total = 0
    use = collections.defaultdict(int)
    info = get_user_info(id)["resources_inv"][type]
    keys = list(info.keys())
    keys.sort(reverse=True)
    for i in keys:
        amount = info[i]
        while total < goal and amount > 0:
            total += int(i)
            use[i] += 1
    return use


def use_resource_items(id, type, cost):
    for k, v in cost.items():
        inc_resource_storage(id, "resources_inv", type, k, -v)
        inc_storage(id, "resources", type, int(k) * v)


def has_enough_resources(id, cost):
    resources = get_user_info(id)["resources"]
    for k, v in cost.items():
        if int(resources[k]) < v:
            return False
    for k, v in cost.items():
        inc_storage(id, "resources", k, -v)
    return True


def get_user_info(id):
    info = player_info.find_one({"_id": id})
    if info:
        return info
    raise NoAccountCreatedError


def total_value(id, storage_name, type):
    info = get_user_info(id)[storage_name][type]
    return sum([int(k) * v for k, v in info.items()])


def inc_storage(id, storage_name, type, amount):
    player_info.update_one({"_id": id}, {"$inc": {f"{storage_name}.{type}": amount}})


def inc_storage_dict(id, storage_name, cost):
    print('h')
    for k, v in cost.items():
        print(storage_name, k, v)
        inc_storage(id, storage_name, k, -v)


def inc_resource_storage(id, storage_name, type, amount_type, amount):
    player_info.update_one({"_id": id}, {"$inc": {f"{storage_name}.{type}.{amount_type}": amount}})


def inc_item(id, item_name, amount):
    player_info.update_one({"_id": id}, {"$inc": {item_name: amount}})


def create_user(id):
    player_info.insert_one(
        {"_id": id, "soldiers_inv": {"horse_man": 0, "archer": 0, "foot_soldier": 0},
         "resources": {"wood": 0, "stone": 0, "ore": 0, "gold": 0, "crystalized_blood": 0},
         "resources_inv":
             {
                 "wood": {"10000": 0,
                          "100000": 0,
                          "500000": 0,
                          "1000000": 0},
                 "stone": {"10000": 0,
                           "100000": 0,
                           "500000": 0,
                           "1000000": 0},
                 "ore": {"10000": 0,
                         "100000": 0,
                         "500000": 0,
                         "1000000": 0},
                 "gold": {"5000": 0,
                          "20000": 0,
                          "100000": 0,
                          "500000": 0},
                 "crystalized_blood": {"50": 0,
                                       "100": 0,
                                       "500": 0,
                                       "1000": 0}}
         })


class LeftButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="testing")

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(content="work")


class Game(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", intents=discord.Intents.all(),
                         activity=discord.Game(name="With DancingElbow"))

        @self.hybrid_command(name="start", description="Start the game!")
        async def start(ctx):
            info = get_user_info(ctx.author.id)
            embed = discord.Embed(title="Error", description="You already have an account!",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)

        @start.error
        async def error(ctx, error):
            if isinstance(error, NoAccountCreatedError):
                embed = discord.Embed(title="Success!",
                                      description="Successfully created your account. Please see /help to start!",
                                      color=discord.Color.green())
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
                create_user(ctx.author.id)
                await ctx.send(embed=embed)

        @self.hybrid_command(name="profile", description="See someone's profile!")
        async def profile(ctx, user: discord.Member = None):
            user = user or ctx.author
            information = get_user_info(user.id)
            embed = discord.Embed(title=f"{user.name} Profile", color=discord.Color.blurple())
            soldiers_message = ""
            for k, v in information["soldiers_inv"].items():
                soldiers_message += k.title().replace("_", " ") + ": " + human_format(v) + "\n"
            embed.add_field(name="Soldiers", value=soldiers_message)
            resources_message = ""
            for k, v in information["resources"].items():
                resources_message += k.title().replace("_", " ") + ": " + human_format(v) + "\n"
            embed.add_field(name="Resources",
                            value=resources_message)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)

        @self.hybrid_command(name="inventory", description="See someone's inventory!", aliases=["inv"])
        async def inventory(ctx, user: discord.Member = None):
            user = user or ctx.author
            info = get_user_info(user.id)
            interaction = View(timeout=60)
            embed1 = discord.Embed(title="Resources", color=discord.Color.blurple())
            for k, v in info["resources_inv"].items():
                message = ""
                for k2, v2 in v.items():
                    message += human_format(int(k2)) + ": " + human_format(int(v2)) + "\n"
                embed1.add_field(name=k.title().replace("_", " "), value=message)
            embed1.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            interaction.add_item(LeftButton())
            await ctx.send(embed=embed1, view=interaction)

        @self.hybrid_command(name="daily", description="Get daily loot")
        @commands.cooldown(1, 72000, commands.BucketType.member)
        async def daily(ctx):
            get_user_info(ctx.author.id)
            inc_resource_storage(ctx.author.id, "resources_inv", "wood", "10000", 1)
            inc_resource_storage(ctx.author.id, "resources_inv", "stone", "10000", 1)
            inc_resource_storage(ctx.author.id, "resources_inv", "ore", "10000", 1)
            inc_resource_storage(ctx.author.id, "resources_inv", "gold", "5000", 1)
            embed = discord.Embed(title="Daily received",
                                  description="Here's what you got:\n1x 10k Wood\n1x 10k Stone\n1x 10k Ore\n1x 5k Gold",
                                  color=discord.Color.green())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)

        @self.hybrid_command(name="train", description="Train some soldiers!")
        @app_commands.choices(type=[
            app_commands.Choice(name="Foot Soldier", value="foot_soldier"),
            app_commands.Choice(name="Archer", value="archer"),
            app_commands.Choice(name="Horse Man", value="horse_man"),
        ])
        async def train(ctx, amount: int, type):
            id = ctx.author.id
            cost = {k: v * amount for k, v in soldiers[type]["cost"].items()}
            await ctx.send(cost)
            canDo = has_enough_resources(id, cost)
            if canDo:
                await ctx.send('you good')
                inc_storage(id, "soldiers_inv", type, int(amount))
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
        async def use(ctx, type, amount: int):
            id = ctx.author.id
            await ctx.send("your total value is " + str(total_value(id, "resources_inv", type)))
            used = dict(get_use_resource_items(id, type, amount))
            if total_value(id, "resources_inv", type) < amount:
                await ctx.send('poor guy literally')
            else:
                await ctx.send("you having enough for the doing")
                use_resource_items(id, type, used)
                await ctx.send(used)

        @self.hybrid_command(name="clear", description="reset data")
        @is_me()
        async def clear(ctx):
            player_info.delete_many({})
            await ctx.send('progress reset')

    async def on_ready(self):
        print(f"Active as {self.user.name} in {len(self.guilds)} server")

    async def setup_hook(self):
        await self.tree.sync()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            embed = discord.Embed(title="Error",
                                  description="You have already used this command. You can use it again in " + seconds_to_time(
                                      error.retry_after) + ".", color=discord.Color.red(),
                                  timestamp=datetime.datetime.now() + datetime.timedelta(seconds=error.retry_after))
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
        if isinstance(error, commands.MissingRole):
            embed = discord.Embed(title="Error", description="You do not have the roles to use this command.",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
        if isinstance(error, NoAccountCreatedError) and ctx.command.name != "start":
            embed = discord.Embed(title="Error",
                                  description="This person has not created an account yet. Start the game with "
                                              "`/start`.",
                                  color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
        else:
            print(error)


bot = Game()

bot.run("OTkzNTEzODQ1NTM4NzAxMzI0.GOpyih.MkQL1WV5ZYSSqLutEV_UJUn780aQOsdFpfKkTY")
