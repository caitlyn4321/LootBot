import random
import time
import datastore
import datetime
import discord
import LootBot
import static
from discord.ext import commands


class QuotesClass:
    filename = "quotes.json"

    def __init__(self, bot, filename=""):
        """Initialize the quotes class"""
        if len(filename) > 0:
            self.filename = filename
        self.quotes_list = datastore.DataStore(self.filename)
        self.bot=bot
        random.seed()

    def load(self, filename=""):
        """Load the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.quotes_list.load(filename)

    def save(self, filename=""):
        """Save the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.quotes_list.save(filename)

    def count(self):
        """Return a count of the quotes"""
        return len(self.quotes_list)

    def getindex(self):
        """Finds the first available index to use"""
        for index in range(1, len(self.quotes_list)):
            if str(index) not in self.quotes_list.keys():
                return index
        return len(self.quotes_list) + 1

    def add(self, quote):
        """Add a quote"""
        quote.append(time.time())
        index = self.getindex()
        self.quotes_list[str(index)] = quote
        self.quotes_list.save()
        return index

    def delete(self, num):
        """Delete a quote"""
        if str(num) in self.quotes_list.keys():
            del self.quotes_list[str(num)]
            self.save()
            return True
        else:
            return False

    def get_quote(self, num):
        """Return a specific quote"""
        if str(num) in self.quotes_list.keys():
            return self.quotes_list[str(num)] + [int(num)]
        else:
            return -1

    def get_random(self):
        """Get a random quote"""
        if len(self.quotes_list) >= 1:
            num = random.choice(list(self.quotes_list.keys()))
            return self.get_quote(num)
        else:
            return -1

    def quote_to_embed(self,result):
        """ Takes a list containing quote values and turns it into an embed that can be posted to discord."""
        thedate = datetime.date.fromtimestamp(result[3])
        thechannel = self.bot.get_channel(result[2])
        themember = thechannel.server.get_member(result[1])
        theauthor = themember.name
        if hasattr(themember, "nick"):
            if themember.nick is not None:
                theauthor = themember.nick
        embed = discord.Embed(title="Quote #{}".format(result[4]), description=result[0])
        embed.set_author(name=theauthor, icon_url=themember.avatar_url)
        embed.set_footer(text="Saved on: {}".format(thedate.strftime("%d %B %y")))
        return embed

    @commands.command(pass_context=True, description="Add a quote")
    async def quote_add(self,ctx, *message: str):
        """Adds a new quote to the database"""
        await self.bot.type()
        num = self.add([' '.join(message), ctx.message.author.id, ctx.message.channel.id])
        await self.bot.say("Quote #{} has been added.".format(num))

    @commands.command(pass_context=True, description="Delete a quote")
    async def quote_del(self, ctx, num: int):
        """Deletes a specific quote from a database"""
        await self.bot.type()
        if await LootBot.check_permissions(ctx.message.author, "Loot Council") is True:
            self.delete(num)
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        else:
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][1])

    @commands.command(pass_context=True, description="get a quote")
    async def quote_get(self, ctx, num: int):
        """Gets a specific quote from the database"""
        await self.bot.type()
        result = self.get_quote(num)
        if result == -1:
            await self.bot.say("Quote #{} is not found..".format(num))
        else:
            await self.bot.say(embed=self.quote_to_embed(result))
            await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True, description="get a quote")
    async def quote(self,ctx):
        """Gets a random quote from the database"""
        await self.bot.type()
        result = self.get_random()
        if result == -1:
            await self.bot.say("There was an issue retrieving a quote")
        else:
            await self.bot.say(embed=self.quote_to_embed(result))
            await self.bot.delete_message(ctx.message)

    @commands.command(description="Show the number of quotes in the database")
    async def quote_count(self):
        """Count the quotes in the database"""
        await self.bot.type()
        result = self.count()
        await self.bot.say(result)


def setup(bot):
    bot.add_cog(QuotesClass(bot=bot))