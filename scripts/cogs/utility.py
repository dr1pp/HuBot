import discord
import asyncio

from discord.ext import commands
import discord_components as components


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True)
    async def clear(self, ctx, limit: int):

        def is_bot(m):
            return m.author == self.bot.user or m.content.startswith(self.bot.command_prefix)

        channel = ctx.message.channel
        deleted = await channel.purge(limit=limit, check=is_bot)
        await ctx.send(f":recycle:  Purged **{len(deleted)}** bot related message(s)", delete_after=10)


class InteractiveMessage:
    def __init__(self, bot: discord.Client, content: str = "", embed: discord.Embed = None):
        self.bot = bot
        self.content = content
        self.embed = embed
        self.items = [[] * 5]
        self.timeout = None


    def add_button(self, row: int, button: components.Button, callback: callable, *args, **kwargs):
        self.items[row].append([button, callback, args, kwargs])


    def add_timeout(self, callback, *args, **kwargs):
        self.timeout = {"callback": callback, "args": args, "kwargs": kwargs}


    def get_components_list(self):
        return [[item[0] for item in row] for row in self.items]


    async def send_message(self, channel):
        self.message = await channel.send(self.content, embed=self.embed, components=self.get_components_list())
        listening = True
        while listening:
            try:
                res = await self.bot.wait_for("button_click")
                if res.message == self.message:
                    comp = res.component
                    for row in self.items:
                        for item in row:
                            if comp.id == item[0].id:
                                await item[1](res, *item[2], **item[3])


            except asyncio.TimeoutError:
                if self.timeout:
                    self.timeout["callback"](*self.timeout["args"], **self.timeout["kwargs"])

def setup(bot):
    bot.add_cog(Utility(bot))
