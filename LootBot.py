import secrets
import discord
import requests
import static
import random
import traceback
from discord.ext import commands

# TODO : Update the bot to be a class for easier unit testing.
# TODO : Create proper unit testing
# TODO : Change the bot.typing() to with statements.

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description=static.description, pm_help=True)
isttson=False

startup_extensions = ["fun","testreplace","quotes","eqserverstatus","LootParse", "polls"]

async def check_permissions(user,name):
    if hasattr(user, "roles"):
        for role in user.roles:
            if name.upper() == role.name.upper():
                print("role found")
                return True
    if str(user.id) == static.myowner:
        print("role not found, but is owner")
        return True
    print("role not found, is not owner")
    return False

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






@bot.command(hidden=True, pass_context=True,
             description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
async def pr(ctx):
    """Prints a message to the console.  Useful for finding out what unicode emotes translate to"""
    await bot.type()
    if str(ctx.message.author.id) == static.myowner:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        print(ctx.message.content)
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])
        await bot.say("This command has only runs for my owner.  There are not a lot of good reasons to run it.")


@bot.command(pass_context=True, description="Ping the bot owner")
async def owner(ctx):
    """Page the bot owner"""
    await bot.type()
    mymention = await bot.get_user_info(static.myowner)
    if str(ctx.message.author.id) == static.myowner:
        await bot.say("You, {} are my owner.".format(mymention.mention))
    else:
        await bot.say(mymention.mention + " is my owner.")

@bot.command(pass_context=True, hidden=True, description="Updates my status message")
async def update_status(ctx, *messages: str):
    """Updats the status that the bot displays"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        await bot.change_presence(game=discord.Game(name=' '.join(messages)))
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])


@bot.command(pass_context=True, hidden=True)
async def say(ctx, *message: str):
    """Repeats something"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        await bot.say(' '.join(message))
        await bot.delete_message(ctx.message)

@bot.command(pass_context=True, hidden=True)
async def load(ctx, extension_name : str):
    """Loads an extension."""
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        try:
            bot.load_extension("modules.{}".format(extension_name))
        except (AttributeError, ImportError) as e:
            await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        await bot.say("{} loaded.".format(extension_name))
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])


@bot.command(pass_context=True, hidden=True)
async def unload(ctx, extension_name : str):
    """Unloads an extension."""
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        bot.unload_extension("modules.{}".format(extension_name))
        await bot.say("{} unloaded.".format(extension_name))
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])

@bot.command(pass_context=True, hidden=True)
async def rl(ctx, extension_name : str):
    """Reloads an extension."""
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        bot.unload_extension("modules.{}".format(extension_name))
        try:
            bot.load_extension("modules.{}".format(extension_name))
        except (AttributeError, ImportError) as e:
            await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        await bot.say("{} reloaded.".format(extension_name))
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension("modules.{}".format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
            traceback.print_exc()
    random.seed()
    bot.run(secrets.BotToken)
