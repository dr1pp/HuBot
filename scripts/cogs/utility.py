import discord
import asyncio
import re

from discord.ext import commands
import discord_components as components
from discord_slash import cog_ext, SlashContext, model


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


    @cog_ext.cog_slash(name="role_colour",
                       description="Change your name colour",
                       guild_ids=[336950154189864961],
                       options=[{
                           "name": "colour",
                           "description": "The hex code of the colour you would like your role to be",
                           "option_type": 3,
                           "required": True
                       }])
    async def role_colour(self, ctx: SlashContext, colour: str):

        if hex_string := get_valid_hex(colour):
            results = self.bot.db.get("SELECT role_id FROM UserData WHERE id = ?", ctx.author_id)
            if len(results) > 0:
                role_id = results[0][0]
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                await role.edit(colour=discord.Colour(hex_string))
            else:
                await ctx.send("You need to claim your role using /claim_role before you can change your colour!",
                               hidden=True)
                return


    @cog_ext.cog_slash(name="claim_role",
                       description="Claim a role to use as your name colour",
                       guild_ids=[336950154189864961],
                       options=[{
                           "name": "role",
                           "description": "The role you would like to claim",
                           "option_type": 8,
                           "required": True
                       }])
    async def claim_role(self, ctx: SlashContext, role: discord.Role):
        self.bot.db.execute("INSERT INTO UserData VALUES (?, ?)", (ctx.author_id, role.id))
        await ctx.send(f":white_check_mark: You have claimed {role.mention} as your colour role",
                       hidden=True)


    @cog_ext.cog_slash(name="reset_db",
                       description="[ADMIN] Reset Database)",
                       guild_ids=[336950154189864961])
    async def reset_db(self, ctx: SlashContext):
        await ctx.defer()
        if ctx.author == self.bot.me:
            confirmation_message = ConfirmationMessage(self.bot, ctx,
                                                       content = "Are you sure you would like to reset the Database?")
            if confirmation_message.get_response():
                self.bot.db.execute("DROP TABLE UserData")
                await ctx.send(":warning: Database reset!")
                self.bot.db.execute("""CREATE TABLE IF NOT EXISTS UserData (
                                                    id INT NOT NULL PRIMARY KEY,
                                                    money INT,
                                                    role_id INT)""")
        else:
            await ctx.send("You do not have the permissions to use this command")


def get_valid_hex(string: str):
    result = re.match(r"^#?[0-9a-fA-F]{6}$", string)
    if result:
        sixteen_int_hex = int("0x" + result.group().replace("#", ""), 16)
        return int(hex(sixteen_int_hex), 0)
    else:
        return None


class CommandOptionType:
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9


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


    async def send_message(self, ctx):
        self.message = await ctx.send(self.content, embed=self.embed, components=self.get_components_list())
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


class ConfirmationMessage:
    def __init__(self, bot: discord.Client, ctx, content: str, timeout: int = 15):
        self.bot = bot
        self.ctx = ctx
        self.content = content
        self.timeout = timeout
        self.choosing = True

    async def get_response(self):
        message = await self.ctx.send(self.content)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=self.timeout)
                if reaction.emoji == "✅" and user == self.ctx.user:
                    await message.delete()
                    return True
                elif reaction.emoji == "❌" and user == self.ctx.user:
                    await message.delete()
                    return False
                else:
                    if user != self.bot.user:
                        await message.remove_reaction(reaction.emoji, user)
            except asyncio.TimeoutError:
                await message.delete()
                return False


def setup(bot):
    bot.add_cog(Utility(bot))
