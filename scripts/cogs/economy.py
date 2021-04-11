from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="hello")
    async def hello(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
