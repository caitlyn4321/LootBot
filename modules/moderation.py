import discord
import static
import traceback
import datastore
import datetime
import asyncio
import concurrent.futures
from discord.ext import commands

# TODO: Change motdtask to a dictionary with task name as keys.

class Moderation:
    filename = "data_motd.json"
    motd_minutes = 120

    def __init__(self, bot, filename=""):
        """Initialize the quotes class"""
        if len(filename) > 0:
            self.filename = filename
        self.motd_list = datastore.DataStore(self.filename)
        self.bot=bot
        print("MOTD Task started.")

    async def on_ready(self):
        if "motdtask" in self.bot.tasks.keys():
            self.bot.tasks['motdtask'].cancel()
        self.bot.tasks['motdtask'] = self.bot.loop.create_task(self.timed_motd())

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

    @commands.command(pass_context=True, description="Set or Unset the MOTD")
    @commands.has_any_role("Admin", "Officer", "Loot Council")
    async def motd_set(self, ctx, *message: str):
        """Sets the MOTD or unsets it if left blank."""
        await self.bot.type()
        if len(message) > 0:
            try:
                msg = await self.bot.get_message(ctx.message.channel, self.motd_list[ctx.message.channel.id][4])
                await self.bot.delete_message(msg)
            except Exception as e:
                pass
            self.motd_list[ctx.message.channel.id] = [datetime.datetime.now().timestamp(),
                                              (datetime.datetime.now() +
                                               datetime.timedelta(minutes=self.motd_minutes)).timestamp(),
                                              ctx.message.author.id,
                                              ' '.join(message),
                                                      None]
            response = self.motd_text([ctx.message.channel.id] + self.motd_list[ctx.message.channel.id])
            newmsg = await self.bot.say(response)
            self.motd_list[ctx.message.channel.id][4] = newmsg.id
            self.motd_list.save()
            try:
                await self.bot.delete_message(ctx.message)
            except:
                pass
        else:
            if ctx.message.channel.id in self.motd_list.keys():
                del self.motd_list[ctx.message.channel.id]
                await self.bot.say("MOTD Deleted")
            else:
                await self.bot.say("No MOTD set for this channel.")
        self.motd_list.save()

    def motd_embed(self,motd_list):
        """ Takes a list containing motd values and turns it into an embed that can be posted to discord."""
        thedate = datetime.datetime.fromtimestamp(motd_list[1])
        thechannel = self.bot.get_channel(motd_list[0])
        themember = thechannel.server.get_member(motd_list[3])
        theauthor = themember.name
        if hasattr(themember, "nick"):
            if themember.nick is not None:
                theauthor = themember.nick
        embed = discord.Embed(title="MOTD for #{}".format(thechannel.name), description=motd_list[4])
        embed.set_author(name=theauthor, icon_url=themember.avatar_url)
        embed.set_footer(text="Set at: {}".format(thedate.strftime("%d %B %y %H:%M")))
        return embed

    def motd_text(self,motd_list):
        thedate = datetime.datetime.fromtimestamp(motd_list[1])
        thechannel = self.bot.get_channel(motd_list[0])
        if thechannel is None:
            print("Error in MOTD.  Channel {} is invalid.\n".format(motd_list[0],motd_list))
            theauthor="UNKNOWN (Aenie Halp)"
        else:
            themember = thechannel.server.get_member(motd_list[3])
            theauthor = themember.name
            if hasattr(themember, "nick"):
                if themember.nick is not None:
                    theauthor = themember.nick
        response="**MOTD**: {}\n**Set by {} on {}**".format(motd_list[4],theauthor,thedate.strftime("%d %B %y %H:%M"))
        return response

    @commands.command(pass_context=True, description="Clear a number of messages")
    async def motd(self, ctx):
        if ctx.message.channel.id in self.motd_list.keys():
            await self.bot.type()
            #embed=self.motd_embed([ctx.message.channel.id]+self.motd_list[ctx.message.channel.id])
            #await self.bot.say(embed=embed)
            response = self.motd_text([ctx.message.channel.id]+self.motd_list[ctx.message.channel.id])
            newmsg = await self.bot.say(response)
            self.motd_list[ctx.message.channel.id][4] = newmsg.id
            self.motd_list[ctx.message.channel.id][1] = (datetime.datetime.now() +
                                             datetime.timedelta(minutes=self.motd_minutes)).timestamp()
            self.motd_list.save()
            await self.bot.delete_message(ctx.message)
        else:
            await self.bot.say("There is no MOTD set")

    async def timed_motd(self):
        """This is the async background task created to process MOTD events."""
        try:
            await self.bot.wait_until_ready()
            while not self.bot.is_closed:
                await asyncio.sleep(10)
                for channelkey in self.motd_list:
                    channel = self.bot.get_channel(channelkey)

                    if datetime.datetime.now() > datetime.datetime.fromtimestamp(int(self.motd_list[channelkey][1])):
                        message_id=0
                        try:
                            async for message in self.bot.logs_from(channel, 1):
                                if hasattr(message,"id"):
                                    message_id=message.id
                        except:
                            pass
                        try:
                            test = int(self.motd_list[channelkey][4])
                        except:
                            print("Message ID saved is not integer: {}".format(self.motd_list[channelkey][4]))
                            self.motd_list[channelkey][4]= -1
                        try:
                            test = int(message_id)
                        except:
                            print("Message ID last is not integer: {}".format(message_id))
                        if int(message_id) != int(self.motd_list[channelkey][4]):
                            if self.motd_list[channelkey][4] is not None or -1:
                                try:
                                    msg = await self.bot.get_message(channel, self.motd_list[channelkey][4])
                                    await self.bot.delete_message(msg)
                                except:
                                    print("Message ID not found: {}".format(self.motd_list[channelkey][4]))
                                self.motd_list[channelkey][4] = None
                            self.motd_list[channelkey][1]=(datetime.datetime.now() +
                                                   datetime.timedelta(minutes=self.motd_minutes)).timestamp()
                            response=self.motd_text([channelkey] + self.motd_list[channelkey])
                            newmsg = await self.bot.send_message(channel, response)
                            self.motd_list[channelkey][4] = newmsg.id
                        self.motd_list[channelkey][1] = (datetime.datetime.now() + datetime.timedelta(
                                                                     minutes=self.motd_minutes)).timestamp()
                        self.motd_list.save()
            print("Bot has closed, zomg")
            return
        except concurrent.futures.CancelledError:
            print ("MOTD Task Cancelled")
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Error in timed MOTD:\n{}'.format( exc))
            traceback.print_exc()
            self.bot.loop.create_task(self.timed_motd())

def setup(bot):
    bot.add_cog(Moderation(bot=bot))


def teardown(bot):
    if "motdtask" in bot.tasks.keys():
        bot.tasks['motdtask'].cancel()
        asyncio.wait_for(bot.tasks['motdtask'],10)
        del bot.tasks['motdtask']
        print("MOTD Task Cancelling")