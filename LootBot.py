import secrets
import discord
import LootParse
import html
import eqserverstatus
import requests
import quotes
import datetime
import asyncio
import sys
import traceback
import static
import random
from discord.ext import commands

# TODO : Update the bot to be a class for easier unit testing.
# TODO : Create proper unit testing
# TODO : Change the bot.typing() to with statements.

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description=static.description, pm_help=True)
loot = LootParse.LootParse()
varQuote = quotes.QuotesClass()
varEQStatus = eqserverstatus.EQServerStatus()
broadcastroom=static.bottest
isttson=False

startup_extensions = ["fun","testreplace"]

def dict_to_embed(starting):
    """Takes an embed dict and returns an embed object"""
    embed = discord.Embed(title=starting['title'], description=starting['description'])
    embed.set_author(name=starting['author']['name'], icon_url=starting['author']['icon_url'])
    if "footer" in starting.keys():
        embed.set_footer(text=starting['footer']['text'])
    else:
        embed.set_footer(text="")
    return embed


def quote_to_embed(result):
    """ Takes a list containing quote values and turns it into an embed that can be posted to discord."""
    thedate = datetime.date.fromtimestamp(result[3])
    thechannel = bot.get_channel(result[2])
    themember = thechannel.server.get_member(result[1])
    theauthor = themember.name
    if hasattr(themember, "nick"):
        if themember.nick is not None:
            theauthor = themember.nick
    embed = discord.Embed(title="Quote #{}".format(result[4]), description=result[0])
    embed.set_author(name=theauthor, icon_url=themember.avatar_url)
    embed.set_footer(text="Saved on: {}".format(thedate.strftime("%d %B %y")))
    return embed

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
    #bot.loop.create_task(timed_status(discord.Object(id=broadcastroom)))


@bot.command(pass_context=True)
async def status(ctx):
    await bot.type()
    result = varEQStatus.check()
    if (result is True) or (result is False):
        await bot.say("Agnarr's current population/status is {} as of {}"
                      .format(varEQStatus.state,varEQStatus.time.strftime("%H:%M")))
    else:
        await bot.say("There is an issue retrieving the current Agnarr status, "
                      "or status calls may be too close together")


@bot.command(hidden=True, pass_context=True,
             description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
async def test(ctx):
    """Runs a test by loading every persons items and reporting failures"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        errors = 0
        try:
            loot.test()
        except:
            errors += 1
        await bot.say("Test complete.  There were {} exceptions seen.".format( errors))
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])
        await bot.say("This command has only runs for my owner.  There are not a lot of good reasons to run it.")


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


@bot.command(description="Clear the memory and start over fresh")
async def reload():
    """Performs a reload of the character table"""
    await bot.type()
    loot.reload()
    await bot.say("reload complete")


@bot.command(pass_context=True,
             description="Looks up the loot history for a person or list of people.  "
                         "Put a question/title in quotes first for a header.",
             aliases=["Lookup"])
async def lookup(ctx, *character: str):
    """The Bot command to perform a character lookup"""
    await do_lookup(ctx, character, True)


async def do_lookup(ctx, character, do_show, embedtitle=""):
    """The function that actually does the lookups.  Shared between multiple functions"""
    await bot.type()
    if not loot.is_loaded():
        await bot.say("I am currently not fully loaded.  Please !reload when I am not broken")
        return

    newchars = []
    charindex = 0
    for char in character:
        if char not in newchars:
            newchars.append(char)

    if "yourmom" in newchars:
        await bot.say("{} is {}".format(ctx.message.author.mention, static.emotes['poop']))
        return

    lookup_list = []
    output = ""
    newoutput=""
    hits = 0
    while charindex < len(newchars):
        char = newchars[charindex]
        if " " in char:
            embedtitle = char
        else:
            try:
                newoutput ="{} {}\n".format(static.emotes['counts'][hits], loot.display(char))
                hits += 1
            except:
                print(sys.exc_info()[0])
                #traceback.print_exc(sys.exc_info())
                if do_show is True:
                    newoutput = "```I don't know who {} is.  I blame you.```\n".format(char)
                else:
                    newoutput = ""

        if len(output + newoutput) > 2000 or charindex == len(newchars) - 1:
            if len(output + newoutput) < 2000:
                output += newoutput
                charindex += 1
            else:
                hits -= 1

            embed = discord.Embed(title=embedtitle, description=output)
            if hasattr(ctx.message.author, "nick"):
                if ctx.message.author.nick is not None:
                    embed.set_author(name=ctx.message.author.nick, icon_url=ctx.message.author.avatar_url)
                else:
                    embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
            else:
                embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
            react = await bot.send_message(ctx.message.channel, embed=embed)
            lookup_list.append(react.id)

            if hits > 1:
                for reaction in static.emotes['counts'][:hits]:
                    await bot.add_reaction(react, reaction)
            if hits == 1:
                await bot.add_reaction(react, static.emotes['checkbox'][0])
                await bot.add_reaction(react, static.emotes['checkbox'][1])
            hits = 0
            output = ""
            newoutput = ""
        else:
            output = output + newoutput
            charindex += 1

    await bot.delete_message(ctx.message)
    if len(newchars)>1:
        await bot.send_message(ctx.message.channel, "Suggested winner, picked at random: {}".format(random.choice(character)))
    return lookup_list


@bot.command(pass_context=True,
             description="Do a simple poll.  Ask your question and list options after."
                         "Anything with spaces must have quotes around it",
             aliases=["Poll"])
async def poll(ctx, question, *options: str):
    """Creates a poll that members can vote on with emotes"""
    await do_poll(ctx, question, options)


@bot.command(pass_context=True,
             description="Do a simple poll.  Ask your question and list options after.  "
                         "Anything with spaces must have quotes around it",
             aliases=["tp"])
async def timed_poll(ctx, question, minutes: int, *options: str):
    """Creates a timed poll that members can vote on with emotes."""
    messages = [await do_poll(ctx, question, options)]
    for message in messages:
        poll_message = await bot.get_message(ctx.message.channel, message)
        if poll_message.embeds:
            embed = dict_to_embed(poll_message.embeds[0])
            embed.set_footer(
                text="{}\nThis poll will close in {} minutes".format(poll_message.embeds[0]['footer']['text'], minutes))
            await bot.edit_message(poll_message, embed=embed)
    bot.loop.create_task(wait_for_poll(ctx, messages, minutes))


async def do_poll(ctx, question, options):
    """The backend shared poll code"""
    if len(options) <= 1:
        await bot.say('You need more than one option to make a poll!')
        return
    if len(options) > 21:
        await bot.say('You cannot make a poll for more than 20 things!')
        return

    if len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
        reactions = static.emotes['checkbox']
    else:
        reactions = static.emotes['counts']

    description = []
    for x, option in enumerate(options):
        description += '\n{} {}'.format(reactions[x], option)
    embed = discord.Embed(title=question, description=''.join(description))
    if hasattr(ctx.message.author, "nick"):
        if ctx.message.author.nick is not None:
            embed.set_author(name=ctx.message.author.nick, icon_url=ctx.message.author.avatar_url)
        else:
            embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
    else:
        embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
    react_message = await bot.say(embed=embed)
    for reaction in reactions[:len(options)]:
        await bot.add_reaction(react_message, reaction)
    embed.set_footer(text='Poll ID: {}'.format(react_message.id))
    await bot.edit_message(react_message, embed=embed)
    await bot.delete_message(ctx.message)
    return react_message.id


@bot.command(pass_context=True, description="Do a simple list.", aliases=["List"])
async def list(ctx, question, *options: str):
    """Creates a list of items with no voting"""
    if len(options) > 21:
        await bot.say('You cannot make a poll for more than 20 things!')
        return
    description = []
    for x, option in enumerate(options):
        description += '\n{} {}'.format(static.emotes['counts'][x], option)
    embed = discord.Embed(title=question, description=''.join(description))
    await bot.say(embed=embed)
    await bot.delete_message(ctx.message)


@bot.command(description="Lookup an item", aliases=["Item"])
async def item(*itemname: str):
    """Attemps very poorly to load an item from the web"""
    await bot.type()

    await bot.say(
        "Just google it,  this command is stupid: http://lmgtfy.com/?q={}".format(html.escape('+'.join(itemname))))
    return


@bot.command(pass_context=True, description="Insults people")
async def insult(ctx):
    """Bot command that uses an amazing insult API to say an insult"""
    await bot.type()
    reqWEB = requests.get('https://insult.mattbas.org/api/en/insult.json').json()

    await bot.say(reqWEB['insult'])
    await bot.delete_message(ctx.message)


@bot.command(pass_context=True, description="Updates my status message")
async def update_status(ctx, *messages: str):
    """Updats the status that the bot displays"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        await bot.change_presence(game=discord.Game(name=' '.join(messages)))
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])


@bot.command(pass_context=True, description="Add a quote")
async def quote_add(ctx, *message: str):
    """Adds a new quote to the database"""
    await bot.type()
    num = varQuote.add([' '.join(message), ctx.message.author.id, ctx.message.channel.id])
    await bot.say("Quote #{} has been added.".format(num))


@bot.command(pass_context=True, description="Delete a quote")
async def quote_del(ctx, num: int):
    """Deletes a specific quote from a database"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        varQuote.delete(num)
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
    else:
        await bot.add_reaction(ctx.message, static.emotes['checkbox'][1])


@bot.command(pass_context=True, description="get a quote")
async def quote_get(ctx, num: int):
    """Gets a specific quote from the database"""
    await bot.type()
    result = varQuote.get_quote(num)
    if result == -1:
        await bot.say("Quote #{} is not found..".format(num))
    else:
        await bot.say(embed=quote_to_embed(result))
        await bot.delete_message(ctx.message)


@bot.command(pass_context=True, description="get a quote")
async def quote(ctx):
    """Gets a random quote from the database"""
    await bot.type()
    result = varQuote.get_random()
    if result == -1:
        await bot.say("There was an issue retrieving a quote")
    else:
        await bot.say(embed=quote_to_embed(result))
        await bot.delete_message(ctx.message)


@bot.command(description="Show the number of quotes in the database")
async def quote_count():
    """Count the quotes in the database"""
    await bot.type()
    result = varQuote.count()
    await bot.say(result)


@bot.command(pass_context=True, description="Lookup by class", aliases=["csearch", "class_lookup"])
async def clookup(ctx, classtype):
    """Perform a lookup on everyone of a single class type"""
    await bot.type()
    result = loot.classes(classtype)
    if len(result) == 0:
        await bot.say("That class wasn't found")
    else:
        await do_lookup(ctx, result, False)


@bot.command(pass_context=True)
async def tally(ctx, *msgid):
    """Tally the votes for a poll"""
    await do_tally(ctx, msgid)


async def do_tally(ctx, ids):
    """This is the backend that supports the tallying of polls and loot council votes"""
    for msgid in ids:
        poll_message = await bot.get_message(ctx.message.channel, msgid)
        if poll_message.embeds:
            title = poll_message.embeds[0]['title']
        else:
            title = "Untitled Poll"
        the_tally = {}
        for reaction in poll_message.reactions:
            if reaction.emoji in static.emotes['counts'] + static.emotes['checkbox']:
                reactors = await bot.get_reaction_users(reaction)
                if len(reactors) > 1:
                    the_tally[reaction.emoji] = []
                    for reactor in reactors:
                        if reactor.id != ctx.message.server.me.id:
                            if ctx.message.server.get_member(reactor.id).nick is not None:
                                the_tally[reaction.emoji].append(ctx.message.server.get_member(reactor.id).nick)
                            else:
                                the_tally[reaction.emoji].append(ctx.message.server.get_member(reactor.id).name)

        output = 'Results of the poll for "{}":\n'.format(title) + \
                 '\n'.join(['{}: ({}) {}'.format(key, len(the_tally[key]), ", ".join(the_tally[key])) for key in
                            sorted(the_tally, key=lambda key: len(the_tally[key]), reverse=True)])
        await bot.send_message(ctx.message.channel, output)


@bot.command(pass_context=True,
             description="Starts a loot council timed poll using the loot history for a person or list of people.  "
                         "Put a question/title in quotes first for a header.",
             aliases=["Lc", "LC"])
async def lc(ctx, title, minutes: int, *character: str):
    """Initiates a loot council vote"""
    messages = await do_lookup(ctx, character, True, title)
    for message in messages:
        poll_message = await bot.get_message(ctx.message.channel, message)
        if poll_message.embeds:
            embed = dict_to_embed(poll_message.embeds[0])
            embed.set_footer(text="This poll will close in {} minutes".format(minutes))
            await bot.edit_message(poll_message, embed=embed)
    bot.loop.create_task(wait_for_poll(ctx, messages, minutes))


async def wait_for_poll(ctx, ids, minutes):
    """This is the async background task created to close the poll out after a specific time."""
    await bot.wait_until_ready()
    await asyncio.sleep(60 * minutes)
    if not bot.is_closed:
        await do_tally(ctx, ids)
        for message in ids:
            poll_message = await bot.get_message(ctx.message.channel, message)
            if poll_message.embeds:
                embed = dict_to_embed(poll_message.embeds[0])
                embed.set_footer(text="Voting is now closed".format(minutes))
                await bot.edit_message(poll_message, embed=embed)
            await bot.clear_reactions(poll_message)
    return

async def timed_status(channel):
    """This is the async background task created to close the poll out after a specific time."""
    try:
        counter=0
        await bot.wait_until_ready()
        while not bot.is_closed:
            await asyncio.sleep(60)
            result = varEQStatus.check()
            if result is False:
                counter+=1
                if counter == 5:
                    await bot.send_message(channel,"Agnarr's current population/status is {} as of {}"
                              .format(varEQStatus.state, varEQStatus.time.strftime("%H:%M")))
            elif result is True:
                counter = 0
            await bot.change_presence(game=discord.Game(name='Agnarr: {} @ {}'.format(varEQStatus.state, varEQStatus.time.strftime("%H:%M"))))
        print("Bot has closed, zomg")
        return
    except:
        traceback.print_exc(sys.exc_info())
        bot.loop.create_task(timed_status(discord.Object(id=broadcastroom)))

@bot.command(pass_context=True, hidden=True)
async def say(ctx, *message: str):
    """Repeats something"""
    await bot.type()
    if await check_permissions(ctx.message.author, "Loot Council") is True:
        await bot.say(' '.join(message))
        await bot.delete_message(ctx.message)



if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension("modules.{}".format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    random.seed()
    bot.run(secrets.BotToken)
