import discord
import static
import asyncio
from discord.ext import commands


class PollsClass:
    def __init__(self, bot):
        """Initialize the polls class"""
        self.bot=bot

    def dict_to_embed(self, starting):
        """Takes an embed dict and returns an embed object"""
        embed = discord.Embed(title=starting['title'], description=starting['description'])
        embed.set_author(name=starting['author']['name'], icon_url=starting['author']['icon_url'])
        if "footer" in starting.keys():
            embed.set_footer(text=starting['footer']['text'])
        else:
            embed.set_footer(text="")
        return embed

    @commands.command(pass_context=True)
    async def tally(self, ctx, *msgid):
        """Tally the votes for a poll"""
        await self.do_tally(ctx, msgid)

    async def do_tally(self,ctx, ids):
        """This is the backend that supports the tallying of polls and loot council votes"""
        for msgid in ids:
            poll_message = await self.bot.get_message(ctx.message.channel, msgid)
            if poll_message.embeds:
                title = poll_message.embeds[0]['title']
            else:
                title = "Untitled Poll"
            the_tally = {}
            for reaction in poll_message.reactions:
                if reaction.emoji in static.emotes['counts'] + static.emotes['checkbox']:
                    reactors = await self.bot.get_reaction_users(reaction)
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
            await self.bot.send_message(ctx.message.channel, output)

    async def wait_for_poll(self, ctx, ids, minutes):
        """This is the async background task created to close the poll out after a specific time."""
        await self.bot.wait_until_ready()
        await asyncio.sleep(60 * minutes)
        if not self.bot.is_closed:
            await self.do_tally(ctx, ids)
            for message in ids:
                poll_message = await self.bot.get_message(ctx.message.channel, message)
                if poll_message.embeds:
                    embed = self.dict_to_embed(poll_message.embeds[0])
                    embed.set_footer(text="Voting is now closed".format(minutes))
                    await self.bot.edit_message(poll_message, embed=embed)
                await self.bot.clear_reactions(poll_message)
        return

    @commands.command(pass_context=True, description="Do a simple list.", aliases=["List"])
    async def list(self, ctx, question, *options: str):
        """Creates a list of items with no voting"""
        if len(options) > 21:
            await self.bot.say('You cannot make a poll for more than 20 things!')
            return
        description = []
        for x, option in enumerate(options):
            description += '\n{} {}'.format(static.emotes['counts'][x], option)
        embed = discord.Embed(title=question, description=''.join(description))
        await self.bot.say(embed=embed)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True,
                 description="Do a simple poll.  Ask your question and list options after."
                             "Anything with spaces must have quotes around it",
                 aliases=["Poll"])
    async def poll(self, ctx, question, *options: str):
        """Creates a poll that members can vote on with emotes"""
        await self.do_poll(ctx, question, options)

    @commands.command(pass_context=True,
                 description="Do a simple poll.  Ask your question and list options after.  "
                             "Anything with spaces must have quotes around it",
                 aliases=["tp"])
    async def timed_poll(self, ctx, question, minutes: int, *options: str):
        """Creates a timed poll that members can vote on with emotes."""
        messages = [await self.do_poll(ctx, question, options)]
        for message in messages:
            poll_message = await self.bot.get_message(ctx.message.channel, message)
            if poll_message.embeds:
                embed = self.dict_to_embed(poll_message.embeds[0])
                embed.set_footer(
                    text="{}\nThis poll will close in {} minutes".format(poll_message.embeds[0]['footer']['text'],
                                                                         minutes))
                await self.bot.edit_message(poll_message, embed=embed)
        self.bot.loop.create_task(self.wait_for_poll(ctx, messages, minutes))

    async def do_poll(self, ctx, question, options):
        """The backend shared poll code"""
        if len(options) <= 1:
            await self.bot.say('You need more than one option to make a poll!')
            return
        if len(options) > 21:
            await self.bot.say('You cannot make a poll for more than 20 things!')
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
        react_message = await self.bot.say(embed=embed)
        for reaction in reactions[:len(options)]:
            await self.bot.add_reaction(react_message, reaction)
        embed.set_footer(text='Poll ID: {}'.format(react_message.id))
        await self.bot.edit_message(react_message, embed=embed)
        await self.bot.delete_message(ctx.message)
        return react_message.id


def setup(bot):
    bot.add_cog(PollsClass(bot=bot))