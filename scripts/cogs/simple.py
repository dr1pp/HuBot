import discord
from discord.ext import commands


class SimpleCog(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command(name="hello")
    async def hello(self, ctx):
        await ctx.send("hie :/")


def setup(client):
    client.add_cog(SimpleCog(client))
