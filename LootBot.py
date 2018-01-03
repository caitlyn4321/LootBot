import secrets
import static
import random
import traceback
import logging
import datetime
import requests
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description=static.description, pm_help=True)
isttson=False

# Setup the logging
bot.logger = logging.getLogger('discord')
bot.logger.setLevel(logging.INFO)

# Setup the log file handler
handler = logging.FileHandler(
    filename=f'Logs\LootBot-{datetime.datetime.now().strftime("%y%m%d%H%M%S")}.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
bot.logger.addHandler(handler)

startup_extensions = ["fun","testreplace","quotes","eqserverstatus","LootParse", "polls","moderation"]


def fetch(url, timeout=10, retries=3):
    counter = retries
    complete = False
    while counter > 0:
        try:
            result = requests.get(url, timeout=timeout)
            complete = True
            break
        except requests.exceptions.Timeout as e:
            counter -= 1
            print('{}: {}'.format(type(e).__name__, e))
            lasterror=e

    if complete:
        return result
    else:
        assert(lasterror)

async def is_bot(user):
    if hasattr(user,"roles"):
        for role in user.roles:
            if "BOTS" == role.name.upper():
                return True
    return False

@bot.event
async def on_ready():
    """ An event handler to print out information once startup is complete"""
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(pass_context=True, description="Ping the bot owner")
async def owner(ctx):
    """Page the bot owner"""
    await bot.type()
    mymention = await bot.get_user_info(static.myowner)
    if str(ctx.message.author.id) == static.myowner:
        await bot.say("You, {} are my owner.".format(mymention.mention))
    else:
        await bot.say(mymention.mention + " is my owner.")

@bot.command(pass_context=True, hidden=True)
@commands.has_any_role("Admin","Officer","Loot Council")
async def load(ctx, extension_name : str):
    """Loads an extension."""
    try:
        bot.load_extension("modules.{}".format(extension_name))
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} loaded.".format(extension_name))


@bot.command(pass_context=True, hidden=True)
@commands.has_any_role("Admin","Officer","Loot Council")
async def unload(ctx, extension_name : str):
    """Unloads an extension."""
    bot.unload_extension("modules.{}".format(extension_name))
    await bot.say("{} unloaded.".format(extension_name))

@bot.command(pass_context=True, hidden=True)
@commands.has_any_role("Admin","Officer","Loot Council")
async def rl(ctx, extension_name : str):
    """Reloads an extension."""
    bot.unload_extension("modules.{}".format(extension_name))
    try:
        bot.load_extension("modules.{}".format(extension_name))
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} reloaded.".format(extension_name))

if __name__ == "__main__":
    bot.tasks={}
    for extension in startup_extensions:
        try:
            bot.load_extension("modules.{}".format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
            traceback.print_exc()
    random.seed()
    bot.run(secrets.BotToken)
