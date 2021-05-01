import discord
from discord.ext import commands

VOICE_ID = 698959931549810764

class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="join")
    async def join(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("You must be in a voice channel to use this command")
            return


def setup(bot):
    bot.add_cog(RadioCog(bot))
