import discord
from discord.ext import commands



class SimpleCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    def setup(self):
        self.client.add_cog(SimpleCog(self.client))



    @commands.command(name="hello")
    async def hello(self, ctx):
        await ctx.send("hie :/")