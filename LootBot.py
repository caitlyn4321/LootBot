import secrets, discord,LootParse, html, re, requests, quotes,datetime, asyncio
from discord.ext import commands


myowner="85512679678033920"
description = '''LootBot - Queen of the loots'''
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description=description,pm_help=True)
loot=LootParse.LootParse()
poop="💩"
counts = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟','🇦', '🇧', '🇨',  '🇩',  '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
checkbox = ['✅', '❌']
varQuote=quotes.quotesClass()

def is_int(num):
    try:
        num=int(num)
        return True
    except:
        return False

def quote_to_embed(result):
    thedate=datetime.date.fromtimestamp(result[3])
    thechannel=bot.get_channel(result[2])
    themember=thechannel.server.get_member(result[1])
    embed = discord.Embed(title=result[0], description="Saved on: "+thedate.strftime("%d %B %y"))
    embed.set_author(name=themember.name, icon_url=themember.avatar_url)
    return embed

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(hidden=True, pass_context=True, description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
async def test(ctx):
    await bot.type()
    if str(ctx.message.author.id) == myowner:
        await bot.add_reaction(ctx.message, checkbox[0])
        errors=0
        try:
            loot.test()
        except:
            errors=errors+1
        await bot.say("Test complete.  There were "+str(errors)+" exceptions seen.")
    else:
        await bot.add_reaction(ctx.message, checkbox[1])
        await bot.say("This command has only runs for my owner.  There are not a lot of good reasons to run it.")

@bot.command(hidden=True, pass_context=True, description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
async def pr(ctx):
    await bot.type()
    if str(ctx.message.author.id) == myowner:
        await bot.add_reaction(ctx.message, checkbox[0])
        errors=0
        try:
            print(ctx.message.content)
        except:
            errors=errors+1
        await bot.say("Test complete.  There were "+str(errors)+" exceptions seen.")
    else:
        await bot.add_reaction(ctx.message, checkbox[1])
        await bot.say("This command has only runs for my owner.  There are not a lot of good reasons to run it.")

@bot.command(pass_context=True, description="Ping the bot owner")
async def owner(ctx):
    await bot.type()
    mymention= await bot.get_user_info(myowner)
    if str(ctx.message.author.id) == myowner:
        await bot.say("You, "+mymention.mention+" are my owner.")
    else:
        await bot.say(mymention.mention + " is my owner.")


@bot.command(description="Clear the memory and start over fresh")
async def reload():
    await bot.type()
    loot.reload()
    await bot.say("reload complete")


@bot.command(pass_context=True,description="Looks up the loot history for a person or list of people.  Put a question/title in quotes first for a header.",aliases=["Lookup"])
async def lookup(ctx,*character : str):
    await do_lookup(ctx,character,True)

async def do_lookup(ctx,character,do_show,embedtitle=""):
    await bot.type()
    if not loot.is_loaded():
        await bot.say("I am currently not fully loaded.  Please !reload when I am not broken")
        return

    newchars=[]
    for char in character:
        if char not in newchars:
            newchars.append(char)

    if "yourmom" in newchars:
        await bot.say(ctx.message.author.mention+" is "+poop)
        return

    lookup_list=[]
    while len(newchars)>0:
        output = ""
        tempchars=newchars[:10]
        newchars=newchars[10:]
        hits=0
        for char in tempchars:
            if " " in char:
                embedtitle=char
            else:
                try:
                    output=output+counts[hits]+" "+str(loot.display(char))+"\n"
                    hits=hits+1
                except:
                    if do_show == True:
                        output=output+"```I don't know who "+char+" is.  I blame you.```\n"

        if len(output)>0:
            embed = discord.Embed(title=embedtitle, description=output)
            react = await bot.say(embed=embed)
            lookup_list.append(react.id)

            if hits>1:
                for reaction in counts[:hits]:
                    await bot.add_reaction(react, reaction)
            if hits==1:
                await bot.add_reaction(react, checkbox[0])
                await bot.add_reaction(react, checkbox[1])
    await bot.delete_message(ctx.message)
    return lookup_list


@bot.command(pass_context=True, description="Do a simple poll.  Ask your question and list options after.  Anything with spaces must have quotes around it",aliases=["Poll"])
async def poll(ctx, question, *options: str):
    if len(options) <= 1:
        await bot.say('You need more than one option to make a poll!')
        return
    if len(options) > 21:
        await bot.say('You cannot make a poll for more than 20 things!')
        return

    if len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
        reactions=checkbox
    else:
        reactions = counts

    description = []
    for x, option in enumerate(options):
        description += '\n{} {}'.format(reactions[x], option)
    embed = discord.Embed(title=question, description=''.join(description))
    react_message = await bot.say(embed=embed)
    for reaction in reactions[:len(options)]:
        await bot.add_reaction(react_message, reaction)
    embed.set_footer(text='Poll ID: {}'.format(react_message.id))
    await bot.edit_message(react_message, embed=embed)
    await bot.delete_message(ctx.message)

@bot.command(pass_context=True, description="Do a simple list.",aliases=["List"])
async def list(ctx, question, *options: str):
    if len(options) > 21:
        await bot.say('You cannot make a poll for more than 20 things!')
        return
    description = []
    for x, option in enumerate(options):
        description += '\n{} {}'.format(counts[x], option)
    embed = discord.Embed(title=question, description=''.join(description))
    await bot.say(embed=embed)
    await bot.delete_message(ctx.message)

@bot.command(description="Lookup an item",aliases=["Item"])
async def item(*itemname : str):
    await bot.type()

    reqWEB = requests.get('http://everquest.allakhazam.com/ihtml?'+html.escape('+'.join(itemname)))
    counter=0
    webLines=reqWEB.text.splitlines()
    itemtitle=""
    image=""

    while counter<len(webLines):
        if "<img " in webLines[counter]:
            m=re.search("src=\"(.+)\" class=\"zam-icon",webLines[counter])
            image=m.group(1)
            m = re.search("iname\">(.+)</span>", webLines[counter+1])
            itemtitle = m.group(1)
            break
        counter=counter+1

    newwebLines=webLines[counter+2:-4]
    outstring='\n'.join(newwebLines)
    outstring=re.sub("<[\w\/\"\ \?\=]+>","",outstring)
    embed = discord.Embed(title=itemtitle, description=outstring)
    embed.set_thumbnail(url=image)
    await bot.say(embed=embed)
    await bot.delete_message(ctx.message)

@bot.command(pass_context=True,description="Insults people")
async def insult(ctx):
    await bot.type()
    reqWEB = requests.get('https://insult.mattbas.org/api/en/insult.json').json()

    await bot.say(reqWEB['insult'])
    await bot.delete_message(ctx.message)

@bot.command(pass_context=True,description="Updates my status message")
async def update_status(ctx,*messages : str):
    await bot.type()
    if str(ctx.message.author.id) == myowner:
        await bot.change_presence(game=discord.Game(name=' '.join(messages)))
        await bot.add_reaction(ctx.message, checkbox[0])
    else:
        await bot.add_reaction(ctx.message, checkbox[1])

@bot.command(pass_context=True,description="Add a quote")
async def quote_add(ctx,*message : str):
    await bot.type()
    num=varQuote.add([' '.join(message),ctx.message.author.id,ctx.message.channel.id])
    await bot.say("Quote #"+str(num)+" has been added.")

@bot.command(pass_context=True,description="Delete a quote")
async def quote_del(ctx,num : int):
    await bot.type()
    if str(ctx.message.author.id) == myowner:
        varQuote.delete(num)
        await bot.add_reaction(ctx.message, checkbox[0])
    else:
        await bot.add_reaction(ctx.message, checkbox[1])

@bot.command(pass_context=True,description="get a quote")
async def quote_get(ctx,num : int):
    await bot.type()
    result=varQuote.get_quote(num)
    if result==-1:
        await bot.say("Quote #"+str(num)+" is not found..")
    else:
        await bot.say(embed=quote_to_embed(result))
        await bot.delete_message(ctx.message)

@bot.command(pass_context=True,description="get a quote")
async def quote(ctx):
    await bot.type()
    result=varQuote.get_random()
    if result==-1:
        await bot.say("There was an issue retrieving a quote")
    else:
        await bot.say(embed=quote_to_embed(result))
        await bot.delete_message(ctx.message)

@bot.command(pass_context=True,description="Show the number of quotes in the database")
async def quote_count(ctx):
    await bot.type()
    result=varQuote.count()
    await bot.say(result)

@bot.command(pass_context=True,description="Lookup by class",aliases=["csearch","class_lookup"])
async def clookup(ctx,classtype):
    await bot.type()
    result=loot.classes(classtype)
    if len(result)==0:
        await bot.say("That class wasn't found")
    else:
        await do_lookup(ctx,result,False)

@bot.command(pass_context=True)
async def tally(ctx, *id):
    await do_tally(ctx,id)

async def do_tally(ctx,ids):
    print(ids)
    for id in ids:
        poll_message = await bot.get_message(ctx.message.channel, id)
        if poll_message.embeds:
            title=poll_message.embeds[0]['title']
        else:
            title="Untitled Poll"
        the_tally={}
        for reaction in poll_message.reactions:
            if reaction.emoji in counts+checkbox:
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
                 '\n'.join(['{}: ({}) {}'.format(key, len(the_tally[key]),", ".join(the_tally[key])) for key in sorted(the_tally, key=lambda key: len(the_tally[key]), reverse=True)])
        await bot.send_message(ctx.message.channel,output)

@bot.command(pass_context=True,description="Starts a loot council timed poll using the loot history for a person or list of people.  Put a question/title in quotes first for a header.",aliases=["Lc","LC"])
async def lc(ctx,title, minutes : int, *character : str):
    messages=await do_lookup(ctx,character,True,title)
    await bot.say("Poll will close in {} minutes.".format(minutes))
    bot.loop.create_task(wait_for_poll(ctx,messages,minutes))


async def wait_for_poll(ctx,ids,minutes):
    await bot.wait_until_ready()
    await asyncio.sleep(60*minutes)
    if not bot.is_closed:
        await do_tally(ctx,ids)
        for id in ids:
            await bot.clear_reactions(await bot.get_message(ctx.message.channel, id))
    return


bot.run(secrets.BotToken)