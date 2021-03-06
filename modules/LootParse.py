import requests
import re
import html
import math
import static
import discord
import sys
import random
import LootBot
import traceback
import asyncio
import aiohttp
import datastore
from discord.ext import commands
from datetime import datetime

# TODO: Ignore KeyError in display, or rewrite the checks to not throw it

class LootParse:
    characters = {}
    item_votes = {}
    notes = {}
    fully_loaded = 0
    filename = "data_loothighlights.json"
    notes_filename = "data_notes.json"


    def __init__(self, bot, filename=""):
        """Startup of the loot parser.  Initial values"""
        if len(filename) > 0:
            self.filename = filename
        self.notes = datastore.DataStore(self.notes_filename)
        self.bot=bot
        random.seed()
        self.bot.loop.create_task(self.reload_loot())

    async def reload_loot(self):
        """Performs the actual reload of the character data"""
        self.loot_highlights = datastore.DataStore(self.filename)
        if "items" not in self.loot_highlights:
            self.loot_highlights['items']={}

        try:
            async with aiohttp.ClientSession() as session:
                req_api = await LootBot.fetch('https://pitfallguild.org/api.php?function=points&mdkpid=2&format=json',session,json=True)
                req_web = await LootBot.fetch('https://pitfallguild.org/index.php/Points/?show_twinks=1',session)
                web_lines = req_web.splitlines()

            self.characters = {}
            for character in req_api['players'].values():
                thischaracter = {"id": character["id"],
                                 'name': character['name'],
                                 'class': character['class_name'],
                                 'items': [],
                                 'items_loaded': 0}
                self.characters[character['name'].upper()] = thischaracter


            counter = 0

            while counter < len(web_lines):
                if "<td ><a href=\"/index.php/Character/" in web_lines[counter]:
                    m = re.search("(\w+)</a>", web_lines[counter])
                    charname = m.group(1)
                    attendance = []
                    p = re.compile("\">(.*)</td>")
                    m = p.search(web_lines[counter + 2])
                    self.characters[charname.upper()]['rank'] = m.group(1)
                    p = re.compile("(\d+)/(\d+)")
                    m = p.search(web_lines[counter + 3])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    m = p.search(web_lines[counter + 4])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    m = p.search(web_lines[counter + 5])
                    att = m.group(1, 2)
                    attendance.append([int(att[0]), int(att[1])])
                    self.characters[charname.upper()]['attendance'] = attendance
                    counter += 4
                counter += 1
            self.fully_loaded = 1
        except requests.exceptions.Timeout as e:
            print('{}: {}'.format(type(e).__name__, e))
            self.fully_loaded = 0
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))
            traceback.print_exc()
            self.fully_loaded = 0

    def is_loaded(self):
        """A function which allows outside functions to know whether the character database is loaded"""
        return self.fully_loaded

    async def get_char(self, character):
        """Returns the raw data for a specific character"""
        await self.cache_items(character)
        return self.characters[character.upper()]

    async def cache_items(self, character):
        """Loads to loot table into the character table for a specific character"""
        if self.characters[character.upper()]['items_loaded'] == 1:
            return
        req_web = await LootBot.fetch('https://pitfallguild.org/index.php/Items/?search_type=buyer&search=' + character)
        web_lines = req_web.splitlines()
        counter = 0

        while counter < len(web_lines):
            if "<td class=\"hiddenSmartphone twinktd\">Items</td>" in web_lines[counter]:
                m = re.search("<td >(\w+)</td>", web_lines[counter - 3])
                charname = m.group(1).upper()

                newitem = {}
                if "img" in web_lines[counter - 2]:
                    m = re.search("> (.+)</span></a></td>", web_lines[counter - 2])
                else:
                    m = re.search("title=\"\w+\">\s?(.+)</span></a></td>", web_lines[counter - 2])
                newitem['name'] = html.unescape(m.group(1))
                m = re.search("\">(.+)</a></td>", web_lines[counter - 1])
                newitem['raid'] = html.unescape(m.group(1))
                m = re.search("<td >(.+)</td>", web_lines[counter - 4])
                raiddate = m.group(1)
                datetime_object = datetime.strptime(raiddate, '%m.%d.%y')
                newitem['date'] = datetime_object.date()
                self.characters[charname]['items'].append(newitem)
            counter += 1
        self.characters[character.upper()]['items_loaded'] = 1

    async def test(self):
        """Performs the item loading test against the characters table"""
        for character in self.characters.keys():
            asyncio.sleep(0.1)
            print(await self.get_char(character))

    async def display(self, character,summary=False):
        """Returns a formatted output for the character data passed to it."""
        cache = await self.get_char(character.upper())
        output = "**{}** ({}/{})".format(cache['name'], cache['class'], cache['rank'])
        thirtyatt = int(cache['attendance'][0][0]) / int(cache['attendance'][0][1])
        emote = static.emotes['90']
        if thirtyatt <= .9:
            emote = static.emotes['75']
        if thirtyatt <= .75:
            emote = static.emotes['50']
        if thirtyatt <= .50:
            emote = static.emotes['35']
        if thirtyatt <= .35:
            emote = static.emotes['0_']
        output +="\t{} 30 Day: **{}% ({}/{})**"\
            .format(emote, math.ceil(100 * int(cache['attendance'][0][0]) / int(cache['attendance'][0][1])),
                    cache['attendance'][0][0], cache['attendance'][0][1])
        output += "\t60 Day: **{}% ({}/{})**"\
            .format(math.ceil(100 * int(cache['attendance'][1][0]) / int(cache['attendance'][1][1])),
                    cache['attendance'][1][0], cache['attendance'][1][1])
        output += "\tLifetime: **{}% ({}/{})**"\
            .format(math.ceil(100 * int(cache['attendance'][2][0]) / int(cache['attendance'][2][1])),
                    cache['attendance'][2][0], cache['attendance'][2][1])
        if character.upper() in self.notes:
            output += "\n\t__Note__: **{}**".format(self.notes[character.upper()])
        output += "\n\t__Items__: **{}**\n".format(len(cache['items']))
        if(summary):
            try:
                if len(cache['items']) > 0:
                    parseditems=[]
                    for x in range(max(self.loot_highlights['items'].values())+1):
                        parseditems.append([])

                    for item in cache['items']:
                        if item['name'] in self.loot_highlights['bosses']:
                            itemname_text="**{}**".format(item['name'])
                        else:
                            itemname_text=item['name']
                        if item['name'] in self.loot_highlights['items'].keys():
                            parseditems[self.loot_highlights['items'][item['name']]].append([itemname_text, item['raid'],
                                                                                             item['date']])
                        else:
                            parseditems[0].append([itemname_text, item['raid'], item['date']])

                    parseditems=parseditems[1:]+[parseditems[0]]
                    for x in range(len(parseditems)):
                        if x == len(parseditems)-1:
                            if len(parseditems[x])>0:
                                output += "\t\t__Not yet categorized__: \t**{}**\n".format(len(parseditems[x]))
                        else:
                            output += "\t\t__Tier {} items__: \t**{}**\n".format(x+1,len(parseditems[x]))
                        if len(parseditems[x]) > 0:
                            if x == 0:
                                for item in parseditems[x]:
                                    output += "\t\t\t{}\t{}\t{}\n".format(item[0].replace("`", "'"), item[1],
                                                                       item[2].strftime("%d %B %y"))
                            else:
                                output += "\t\t\t{}\t{}\t{}\n".format(parseditems[x][0][0].replace("`", "'"), parseditems[x][0][1],
                                                                    parseditems[x][0][2].strftime("%d %B %y"))
                        #output += "\n"
            except Exception as e:
                exc = '{}: {}'.format(type(e).__name__, e)
                print('Error in summary:\n{}'.format(exc))
                traceback.print_exc()

        else:
            for item in cache['items']:
                itemfound = False
                templine = "\t\t{}\t{}\t{}".format(item['name'].replace("`","'"), item['raid'], item['date'].strftime("%d %B %y"))
                for boss in self.loot_highlights['bosses'].keys():
                    if item['name'] in self.loot_highlights['bosses'][boss]:
                        output += "**{}\t(__{}__)**\n".format(templine,boss)
                        itemfound = True
                if not itemfound:
                    output +="{}\n".format(templine)

        return output

    def classes(self, classtype):
        """Search the characters table for a list of names of those matching a class"""
        results = []
        for character in self.characters.values():
            doappend = ""
            if character['class'].upper() == classtype.upper():
                doappend = character['name']
            if "rank" in character.keys():
                if character['rank'].upper() == classtype.upper():
                    doappend = character['name']
            if len(doappend) > 0:
                results.append(doappend)
        return results

    @commands.command(pass_context=True, description="Lookup by class", aliases=["csearch", "class_lookup"])
    async def clookup(self, ctx, classtype):
        """Perform a lookup on everyone of a single class type"""
        await self.bot.type()
        result = self.classes(classtype)
        if len(result) == 0:
            await self.bot.say("That class wasn't found")
        else:
            await self.do_lookup(ctx, result, False)

    @commands.command(pass_context=True, description="Lookup by class",aliases=["csum"])
    async def csummary(self, ctx, classtype):
        """Perform a summary lookup on everyone of a single class type"""
        await self.bot.type()
        result = self.classes(classtype)
        if len(result) == 0:
            await self.bot.say("That class wasn't found")
        else:
            await self.do_lookup(ctx, result, False, summary=True)

    @commands.command(description="Clear the memory and start over fresh")
    async def reload(self):
        """Performs a reload of the character table"""
        await self.bot.type()
        starttime = datetime.now()
        await self.reload_loot()
        if self.is_loaded():
            await self.bot.say("Reload complete in {}s".format((datetime.now() - starttime).seconds))
        else:
            await self.bot.say("Reload timed out in {}s (not my fault)".format((datetime.now() - starttime).seconds))

    @commands.command(pass_context=True,
                 description="Looks up the loot history for a person or list of people.  "
                             "Put a question/title in quotes first for a header.",
                 aliases=["Lookup"])
    async def lookup(self, ctx, *character: str):
        """The Bot command to perform a character lookup"""
        await self.do_lookup(ctx, character, True)

    @commands.command(pass_context=True,aliases=["sum"])
    async def summary(self, ctx, *character: str):
        """The Bot command to perform a character summary lookup"""
        await self.do_lookup(ctx, character, True, summary=True)

    async def charsort(self,character):
        returnvalue = 0
        try:
            cache = await self.get_char(character.upper())
            if len(cache['items']) > 0:

                attendance=int(cache['attendance'][0][0]) / int(cache['attendance'][0][1])
                result=datetime.now().timestamp()-datetime.combine(cache['items'][0]['date'],datetime.min.time()).timestamp()
                returnvalue = result*attendance
        except Exception as e:
            pass

        return returnvalue

    async def do_lookup(self, ctx, character, do_show, embedtitle="",summary=False):
        """The function that actually does the lookups.  Shared between multiple functions"""
        await self.bot.type()
        starttime = datetime.now()
        sender=ctx.message.author.name
        if hasattr(ctx.message.author, "nick"):
            if ctx.message.author.nick is not None:
                sender=ctx.message.author.nick

        print("[{}] {} in {} is looking up: {}".format(datetime.now().replace(microsecond=0), sender,
                                                       ctx.message.channel.name,' '.join(character)))
        if not self.is_loaded():
            await self.bot.say("I am currently not fully loaded.  Please !reload when I am not broken")
            return

        try:
            newchars = {}
            charindex = 0
            for char in character:
                if char not in newchars:
                    newchars[char]=await self.charsort(char)

            newchars=sorted(newchars, key=newchars.__getitem__)

            if "yourmom" in newchars:
                await self.bot.say("{} is {}".format(ctx.message.author.mention, static.emotes['poop']))
                return

            lookup_list = []
            output = ""
            newoutput = ""
            hits = 0
            while charindex < len(newchars):
                char = newchars[charindex]
                if " " in char and not len(embedtitle)>0:
                    embedtitle = char
                else:
                    try:
                        trunclimit=1990
                        fulltext=await self.display(char,summary=summary)
                        newoutput = "{} {}\n".format(static.emotes['counts'][hits], fulltext[:trunclimit])
                        hits += 1
                        if len(newoutput) > trunclimit:
                            newoutput+="..."
                    except KeyError:
                        # traceback.print_exc(sys.exc_info())
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
                    react = await self.bot.send_message(ctx.message.channel, embed=embed)
                    lookup_list.append(react.id)

                    if hits > 1:
                        for reaction in static.emotes['counts'][:hits]:
                            await self.bot.add_reaction(react, reaction)
                    if hits == 1:
                        await self.bot.add_reaction(react, static.emotes['checkbox'][0])
                        await self.bot.add_reaction(react, static.emotes['checkbox'][1])
                    hits = 0
                    output = ""
                    newoutput = ""
                else:
                    output = output + newoutput
                    charindex += 1
            try:
                await self.bot.delete_message(ctx.message)
            except:
                pass
            if len(newchars) > 1:
                await self.bot.say("\n**Lookup complete** ({}s)".format((datetime.now() - starttime).seconds))
            return lookup_list
        except Exception as e:
            self.bot.say("I broke and will not be responding to you {}.".format(sender))

    @commands.command(name="test", hidden=True, pass_context=True,
                 description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def test_parse(self, ctx):
        """Runs a test by loading every persons items and reporting failures"""
        await self.bot.type()
        await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        errors = 0
        try:
            await self.test()
        except:
            traceback.print_exc()
            errors += 1
        await self.bot.say("Test complete.  There were {} exceptions seen.".format(errors))

    @commands.command(pass_context=True, description="Adds an item to highlight")
    @commands.has_any_role("Admin", "Officer")
    async def highlight_add(self, ctx,tier : int,  *msg):
        """!highlight_add <tier> <name>"""
        highlight = ' '.join(msg)
        if highlight not in self.loot_highlights['items'].keys():
            self.loot_highlights['items'][highlight]=tier
            await self.bot.say("\"{}\" added as tier {}".format(highlight,tier))
            self.loot_highlights.save()
        else:
            await self.bot.say("\"{}\" is already on the list at tier {}".format(highlight,self.loot_highlights['items'][highlight]))

    @commands.command(pass_context=True, description="Deletes an item highlight")
    @commands.has_any_role("Admin", "Officer")
    async def highlight_del(self, ctx, *msg):
        """!highlight_del <name>"""
        highlight = ' '.join(msg)
        if highlight not in self.loot_highlights['items'].keys():
            await self.bot.say("\"{}\" is not on the list".format(highlight))
        else:
            del self.loot_highlights['items'][highlight]
            self.loot_highlights.save()
            await self.bot.say("\"{}\" has been removed".format(highlight))

    @commands.command(pass_context=True, description="Opens an item vote")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def voteopen(self, ctx, itemname, *desc):
        """!voteopen <Item> <Description of Item>"""
        if itemname.upper() in self.item_votes:
            output="That item is already on the list"
            for item,info in self.item_votes.items():
                output += "\n\t{}\t\t\t{}".format(item,info[0])
            await self.bot.say(output)
        else:
            self.item_votes[itemname.upper()] = [' '.join(desc),[]]
            await self.bot.say("Voting opened: {} ({})".format(itemname,' '.join(desc)))

    @commands.command(pass_context=True, description="Closes an item vote")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def voteclose(self, ctx, itemname):
        """!voteclose <Item>"""
        if itemname.upper() in self.item_votes:
            output = "Vote \"{}\" ({}) is now closed.".format(itemname.upper(), self.item_votes[itemname.upper()][0])
            if len(self.item_votes[itemname.upper()][1]) > 0:
                names=[]
                output += "\n"
                for charname,discordname in self.item_votes[itemname.upper()][1]:
                    output += "\t{} ({})".format(charname,discordname)
                    names.append(charname)
                await self.bot.say(output)
                await self.do_lookup(ctx, names ,True,"{}: {}".format(itemname,self.item_votes[itemname.upper()][0]), True)
            else:
                output += " There were no names entered."
                await self.bot.say(output)
            del self.item_votes[itemname.upper()]
        else:
            output = "Item \"{}\" is not an open vote.".format(itemname)
            if len(self.item_votes) >0:
                output += "  The current votes are:"
                for item, info in self.item_votes.items():
                    output += "\n\t{}\t\t\t{}".format(item, info[0])
            else:
                output += "  There are currently no open votes"
            await self.bot.say(output)

    @commands.command(pass_context=True, description="List open item votes")
    async def votelist(self, ctx):
        """!votelist"""
        if len(self.item_votes) > 0:
            output = "Here is a list of votes that are open,  the first work is the vote name,"
            " the second is the description.\n\tUSAGE: !vote <name of vote> <Character name>"

            for item,info in self.item_votes.items():
                output += "\n\t{}\t\t\t{}".format(item,info[0])
            await self.bot.say(output)
        else:
            await self.bot.say("There are no votes currently open")

    @commands.command(pass_context=True, description="Put a characters name in for an item")
    async def vote(self, ctx,itemname,*chars):
        """!vote <votename> <character>"""
        if itemname.upper() in self.item_votes:
            sender = ctx.message.author.name
            if hasattr(ctx.message.author, "nick"):
                if ctx.message.author.nick is not None:
                    sender = ctx.message.author.nick
            for charname in chars:
                if charname.upper() in self.item_votes[itemname.upper()][1]:
                    await self.bot.say("Character {} is already in the vote {}.".format(charname,itemname.upper()))
                else:
                    self.item_votes[itemname.upper()][1].append([charname.upper(),sender])
                    await self.bot.say("{} has added {} to vote {}".format(sender,charname,itemname))
        else:
            await self.bot.say("{} is not a valid vote.  Please do a !votelist for the correct info.".format(itemname))

    @commands.command(pass_context=True, description="Closes an item vote")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def voteshow(self, ctx, itemname):
        """!voteclose <Item>"""
        if itemname.upper() in self.item_votes:
            output = "Current results for {} ({}).".format(itemname.upper(), self.item_votes[itemname.upper()][0])
            if len(self.item_votes[itemname.upper()][1]) > 0:
                output += "\n"
                for charname,discordname in self.item_votes[itemname.upper()][1]:
                    output += "\t{} ({})".format(charname,discordname)
            else:
                output += " There were no names entered."
            await self.bot.say(output)
        else:
            output = "Item \"{}\" is not an open vote.".format(itemname)
            if len(self.item_votes) >0:
                output += "  The current votes are:"
                for item, info in self.item_votes.items():
                    output += "\n\t{}\t\t\t{}".format(item, info[0])
            else:
                output += "  There are currently no open votes"
            await self.bot.say(output)

    @commands.command(pass_context=True, description="Set or Unset a players loot note")
    async def note(self, ctx, character:str, *message: str):
        """Sets player notes with !note <name> <note>"""
        await self.bot.type()
        if len(message) > 0:
            note = ' '.join(message)
            note = note[:102]
            self.notes[character.upper()] = note
            await self.bot.say("Note for {} set: {}".format(character,note))
            await self.bot.delete_message(ctx.message)
        else:
            if character.upper() in self.notes.keys():
                del self.notes[character.upper()]
                await self.bot.say("Note for {} Deleted".format(character))
            else:
                await self.bot.say("{} has no note set".format(character))
        self.notes.save()

    @commands.command( description="List player notes")
    async def notelist(self):
        """List player notes"""
        await self.bot.type()
        if len(self.notes) > 0:
            output = "There are {} notes:".format(len(self.notes))
            for name,note in self.notes.items():
                newaddition = "\t{} : \t{}".format(name,note)
                if len(newaddition+"\n"+output) > 2000:
                    await self.bot.say(output)
                    output=newaddition
                else:
                    output += "\n"+newaddition
            await self.bot.say(output)
        else:
            await self.bot.say("There are currently no notes set")


def setup(bot):
    bot.add_cog(LootParse(bot=bot))