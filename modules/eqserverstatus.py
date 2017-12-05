import requests
import datetime
import datastore
import LootBot
import asyncio
import discord
import static
import traceback
from discord.ext import commands

class EQServerStatus:
    url="https://census.daybreakgames.com/s:dgc/json/get/global/game_server_status?game_code=eq&name={}&c%3Ashow=name" \
        "%2Clast_reported_state%2Clast_reported_time"

    def __init__(self, bot, servername="Agnarr"):
        """Initialize the class"""
        self._servername = servername
        self.loaded = 0
        self.state = ""
        self.time = 0
        self.lastchecked = 0
        self._update()
        self.minseconds = 10
        self.bot=bot
        self.broadcastroom = static.bottest

    def _update(self):
        try:
            changed = False
            req_api = requests.get(self.url.format(self._servername),timeout=5).json()

            if int(req_api['returned'])>0:
                if req_api['game_server_status_list'][0]['last_reported_state'] != self.state:
                    changed = True
                    self.state = req_api['game_server_status_list'][0]['last_reported_state']
                self.time = datetime.datetime.fromtimestamp(
                    int(req_api['game_server_status_list'][0]['last_reported_time']))
            else:
                changed = None
            self.lastchecked=datetime.datetime.now()
            self.loaded=1
            return changed
        except requests.exceptions.ReadTimeout as e:
            print('{}: {}'.format(type(e).__name__, e))
            self.loaded=0
            return None
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))
            traceback.print_exc()
            self.loaded=0
            return None

    def check(self):
        if datetime.datetime.now() < self.lastchecked + datetime.timedelta(seconds=self.minseconds):
            return None
        return self._update()

    async def timed_status(self,channel):
        """This is the async background task created to close the poll out after a specific time."""
        try:
            counter = 0
            await self.bot.wait_until_ready()
            while not self.bot.is_closed:
                await asyncio.sleep(60)
                result = self.check()
                if result is False:
                    counter += 1
                    if counter == 5:
                        await self.bot.send_message(channel, "Agnarr's current population/status is {} as of {}"
                                               .format(self.state, self.time.strftime("%H:%M")))
                elif result is True:
                    counter = 0
                await self.bot.change_presence(game=discord.Game(
                    name='Agnarr: {} @ {}'.format(self.state, self.time.strftime("%H:%M"))))
            print("Bot has closed, zomg")
            return
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Error in timed status:\n{}'.format( exc))
            traceback.print_exc()
            self.bot.loop.create_task(self.timed_status(discord.Object(id=self.broadcastroom)))

    @commands.command(pass_context=True)
    async def status(self,ctx):
        await self.bot.type()
        result = self.check()
        if (result is True) or (result is False):
            await self.bot.say("Agnarr's current population/status is {} as of {}"
                          .format(self.state, self.time.strftime("%H:%M")))
        else:
            await self.bot.say("There is an issue retrieving the current Agnarr status, "
                          "or status calls may be too close together")

    async def on_ready(self):
        """ An event handler to print out information once startup is complete"""
        self.bot.loop.create_task(self.timed_status(discord.Object(id=self.broadcastroom)))


def setup(bot):
    bot.add_cog(EQServerStatus(bot=bot))