import discord
import static
import traceback
from discord.ext import commands

class Moderation:
    def __init__(self, bot):
        """Initialize the class"""
        self.bot=bot

    @commands.command(pass_context=True)
    @commands.has_any_role("Admin","Officer","Loot Council")
    async def say(self, ctx, *message: str):
        """Repeats something"""
        await self.bot.type()
        await self.bot.say(' '.join(message))
        await self.bot.delete_message(ctx.message)

    @commands.command(hidden=True, pass_context=True,
                 description="Run a test by pulling the loot lists for all listed members and check to see if I crash.")
    async def pr(self, ctx):
        """Prints a message to the console.  Useful for finding out what unicode emotes translate to"""
        await self.bot.type()
        if str(ctx.message.author.id) == static.myowner:
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])
            print(ctx.message.content)
        else:
            await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][1])
            await self.bot.say("This command has only runs for my owner.  There are not a lot of good reasons to run it.")

    @commands.command(pass_context=True, description="Updates my status message")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def update_status(self, ctx, *messages: str):
        """Updats the status that the bot displays"""
        await self.bot.type()
        await self.bot.change_presence(game=discord.Game(name=' '.join(messages)))
        await self.bot.add_reaction(ctx.message, static.emotes['checkbox'][0])

    @commands.command(pass_context=True, description="Clear a number of messages")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def purge(self, ctx, number: int):
        """Deletes a number of messages"""
        await self.bot.type()
        await self.bot.purge_from(ctx.message.channel, limit=number+1)

def setup(bot):
    bot.add_cog(Moderation(bot=bot))