import asyncio
import random
import LootBot
from time import strftime

import discord
from discord.ext import commands
import requests




class Fun:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def roll(self, ctx, *, dice: str ='1d6'):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except ValueError:
            await self.bot.say('Format has to be in NdN!')
            return

        author = ctx.message.author
        title = 'Here are your dice results!'
        em = discord.Embed(author=author, title=title)
        for r in range(rolls):
            em.add_field(name="Dice #" + str(r+1), value=str(random.randint(1, limit)))
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def flip(self, ctx):
        """ Flips a coin."""
        author = ctx.message.author
        em = discord.Embed(author=author)
        coin = random.randint(1, 2)
        if coin == 1:
            em.set_image(url="https://www.usmint.gov/wordpress/wp-content/uploads/2017/03/2017-lincoln-penny-uncirculated-reverse-300x300.jpg")
            await self.bot.say(embed=em)
        elif coin == 2:
            em.set_image(url="https://www.usmint.gov/wordpress/wp-content/uploads/2017/03/2017-lincoln-penny-proof-obverse-san-francisco-300x300.jpg")
            await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def ask(self, ctx, *, s: str):
        """ Asks wolfram alpha"""
        s.replace(' ', '+')
        req = requests.get("http://api.wolframalpha.com/v1/result?appid=RPYQ54-Q3W9QJKWR9&i=" + s,timeout=5)
        author = ctx.message.author
        em = discord.Embed(description=req.text, author=author)
        await self.bot.say(embed=em)


    @commands.command(pass_context=True, description='Ask the Bot to choose one')
    async def choose(self, ctx, *choices: str):
        """Chooses between multiple choices."""
        author = ctx.message.author
        em = discord.Embed(author=author, description=random.choice(choices))
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, name='8ball')
    async def ball(self, ctx):
        """ Ask the 8Ball """
        answers = ['It is certain', 'It is decidedly so', 'Without a doubt',
                   'Yes, definitely', 'You may rely on it', 'As I see it, yes',
                   'Most likely', 'Outlook good', 'Yes', 'Signs point to yes',
                   'Reply hazy try again', 'Ask again later',
                   'Better not tell you now', 'Cannot predict now',
                   'Concentrate and ask again', 'Don\'t count on it',
                   'My reply is no', 'My sources say no',
                   'Outlook not so good', 'Very doubtful']

        author = ctx.message.author
        em = discord.Embed(author=author, description=random.choice(answers))
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, description="Insults people", aliases=["play","queue"])
    async def insult(self, ctx,tts=""):
        """Use an amazing insult API to say an insult"""
        await self.bot.type()
        reqWEB = await LootBot.fetch('https://insult.mattbas.org/api/en/insult.json',json=True)

        if tts=="tts":
            bTTS=True
        else:
            bTTS=False
        await self.bot.say(reqWEB['insult'],tts=bTTS)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True, description="Searches for an item")
    async def item(self, ctx,*itemname: str):
        """Searches for an item"""
        await self.bot.type()

        await self.bot.say('http://lmgtfy.com/?q='+'%20'.join(itemname))
        await self.bot.delete_message(ctx.message)



def setup(bot):
    bot.add_cog(Fun(bot))