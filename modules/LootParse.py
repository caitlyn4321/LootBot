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
import datastore
from discord.ext import commands
from datetime import datetime

# TODO: Ignore KeyError in display, or rewrite the checks to not throw it

class LootParse:
    characters = {}
    fully_loaded = 0
    filename = "data_loothighlights.json"

    def __init__(self, bot, filename=""):
        """Startup of the loot parser.  Initial values"""
        if len(filename) > 0:
            self.filename = filename
        self.bot=bot
        random.seed()
        self.reload_loot()

    def reload_loot(self):
        """Performs the actual reload of the character data"""
        self.loot_highlights = datastore.DataStore(self.filename)
        if "items" not in self.loot_highlights:
            self.loot_highlights['items']={}

        try:
            req_api = LootBot.fetch('https://pitfallguild.org/api.php?function=points&format=json').json()
            req_web = LootBot.fetch('https://pitfallguild.org/index.php/Points/?show_twinks=1')

            self.characters = {}

            for character in req_api['players'].values():
                thischaracter = {"id": character["id"],
                                 'name': character['name'],
                                 'class': character['class_name'],
                                 'items': [],
                                 'items_loaded': 0}
                self.characters[character['name'].upper()] = thischaracter

            web_lines = req_web.text.splitlines()
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

    def get_char(self, character):
        """Returns the raw data for a specific character"""
        self.cache_items(character)
        return self.characters[character.upper()]

    def cache_items(self, character):
        """Loads to loot table into the character table for a specific character"""
        if self.characters[character.upper()]['items_loaded'] == 1:
            return
        req_web = LootBot.fetch('https://pitfallguild.org/index.php/Items/?search_type=buyer&search=' + character)
        counter = 0
        web_lines = req_web.text.splitlines()

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
            print(self.get_char(character))

    def display(self, character,summary=False):
        """Returns a formatted output for the character data passed to it."""
        cache = self.get_char(character.upper())
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
        output += "\n\t__Items__: **{}**\n".format(len(cache['items']))
        if(summary):
            try:
                if len(cache['items']) > 0:
                    parseditems=[]
                    for x in range(max(self.loot_highlights['items'].values())+1):
                        parseditems.append([])

                    for item in cache['items']:
                        if item['name'] in self.loot_highlights['items'].keys():
                            parseditems[self.loot_highlights['items'][item['name']]].append([item['name'], item['raid'],
                                                                                             item['date']])
                        else:
                            parseditems[0].append([item['name'], item['raid'], item['date']])

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
                templine = "\t\t{}\t{}\t{}".format(item['name'].replace("`","'"), item['raid'], item['date'].strftime("%d %B %y"))
                if item['name'] in self.loot_highlights['items'].keys():
                    output += "**{}**\n".format(templine)
                else:
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
        self.reload_loot()
        await self.bot.say("reload complete")

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

    async def do_lookup(self, ctx, character, do_show, embedtitle="",summary=False):
        """The function that actually does the lookups.  Shared between multiple functions"""
        await self.bot.type()
        sender=ctx.message.author.name
        if hasattr(ctx.message.author, "nick"):
            if ctx.message.author.nick is not None:
                sender=ctx.message.author.nick

        print("[{}] {} in {} is looking up: {}".format(datetime.now().replace(microsecond=0), sender,
                                                       ctx.message.channel.name,' '.join(character)))
        if not self.is_loaded():
            await self.bot.say("I am currently not fully loaded.  Please !reload when I am not broken")
            return

        newchars = []
        charindex = 0
        for char in character:
            if char not in newchars:
                newchars.append(char)

        if "yourmom" in newchars:
            await self.bot.say("{} is {}".format(ctx.message.author.mention, static.emotes['poop']))
            return

        lookup_list = []
        output = ""
        newoutput = ""
        hits = 0
        while charindex < len(newchars):
            char = newchars[charindex]
            if " " in char:
                embedtitle = char
            else:
                try:
                    trunclimit=1990
                    newoutput = "{} {}\n".format(static.emotes['counts'][hits], self.display(char,summary=summary)[:trunclimit])
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
        return lookup_list

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

def setup(bot):
    bot.add_cog(LootParse(bot=bot))