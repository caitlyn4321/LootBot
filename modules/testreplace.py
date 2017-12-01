import datastore
import LootBot
from discord.ext import commands

class WordResponse:
    filename = "data_responses.json"

    def __init__(self, filename="", bot=None):
        """Initialize the quotes class"""
        self.bot=bot
        if len(filename) > 0:
            self.filename = filename
        self.response_list = datastore.DataStore(self.filename)

    def load(self, filename=""):
        """Load the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.response_list.load(filename)

    def save(self, filename=""):
        """Save the JSON formatted quotes database"""
        if len(filename) == 0:
            filename = self.filename
        self.response_list.save(filename)

    def count(self):
        """Return a count of the quotes"""
        return len(self.response_list)

    def add(self, word: str, phrase):
        """Add a quote"""
        self.response_list[word.upper()] = ' '.join(list(phrase))
        self.response_list.save()

    def delete(self, word: str):
        """Delete a quote"""
        if word.upper() in self.response_list.keys():
            del self.response_list[word.upper()]
            self.save()
            print(self.response_list)
            return True
        else:
            return False

    def check(self, words: str):
        """Return a specific quote"""
        for word in self.response_list.keys():
            if word.upper() in words.upper():
                return self.response_list[word.upper()]
        return None

    async def on_message(self,message):
        """ Process messages"""
        await self.bot.process_commands(message)
        if message.author != self.bot.user:
            if await LootBot.is_bot(message.author) is False:
                response = self.check(message.content)
                if response is not None:
                    await self.bot.send_message(message.channel, response, tts=LootBot.isttson)

    @commands.command(pass_context=True)
    async def response_add(self,ctx, word: str, *words: str):
        """Repeats something"""
        if await LootBot.check_permissions(ctx.message.author, "Loot Council") is True:
            await self.bot.type()
            self.add(word, words)
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        else:
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][1])

    @commands.command(pass_context=True)
    async def response_del(self,ctx, word: str):
        """Repeats something"""
        if await LootBot.check_permissions(ctx.message.author, "Loot Council") is True:
            await self.bot.type()
            self.delete(word)
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
        else:
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][1])


def setup(bot):
    bot.add_cog(WordResponse(bot=bot))