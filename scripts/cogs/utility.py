import random

import discord
import asyncio
import re
import datetime

from dataclasses import dataclass
from collections import namedtuple
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.model import SlashCommandOptionType, ButtonStyle
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.utils import manage_components
from discord_slash.utils.manage_components import create_button, create_actionrow


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @cog_ext.cog_slash(name="cleanup",
                       description="Clean up chat messages from the current channel",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(name="limit",
                                         option_type=SlashCommandOptionType.INTEGER,
                                         description="How many messages you would like to scan through",
                                         required=False)
                       ])
    async def cleanup(self, ctx, limit: int):

        def is_bot(m):
            return m.author == self.bot.user or m.content.startswith(self.bot.command_prefix)

        channel = ctx.message.channel
        deleted = await channel.purge(limit=limit, check=is_bot)
        await ctx.send(f":recycle:  Purged **{len(deleted)}** bot related message(s)", delete_after=10)


    @cog_ext.cog_slash(name="d",
                       description="Roll a [sides] sided dice [rolls] times",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(name="sides",
                                         description="Number of faces for each die",
                                         option_type=SlashCommandOptionType.INTEGER,
                                         required=False),
                           create_option(name="rolls",
                                         description="Number of dice you would like to roll",
                                         option_type=SlashCommandOptionType.INTEGER,
                                         required=False)
                       ])
    async def dice_roll(self, ctx: SlashContext, sides: int = 6, rolls: int = 1):
        await ctx.defer()
        values = [random.randint(1, sides+1) for i in range(1, rolls+1)]
        embed = discord.Embed(title="Dice Roll :game_die:",
                              description=f"Rolled {rolls} {sides} sided die",
                              colour=0xEA596E)
        embed.add_field(name="Roll #", value="\n".join(range(1, len(values))), inline=True)
        embed.add_field(name="Result", value="\n".join([str(val) for val in values]), inline=True)
        if rolls > 1:
            embed.add_field(name="Total", value=str(sum(values)), inline=False)
            embed.add_field(name="Average", value=str(sum(values) / len(values)), inline=True)
        await ctx.send(embed=embed)


    @cog_ext.cog_slash(name="set_colour",
                       description="Change your name colour",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(name="colour",
                                         description="Hex code of the colour you would like to change your role to",
                                         option_type=SlashCommandOptionType.STRING,
                                         required=True)
                       ])
    async def set_colour(self, ctx: SlashContext, colour: str):
        await ctx.defer()
        if hex_string := get_valid_hex(colour):
            results = self.bot.db.get("SELECT role_id FROM UserData WHERE id = ?", (ctx.author_id,))
            print(results)
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
                       options=[
                           create_option(
                               name="role",
                               description="The role you would like to claim",
                               option_type=SlashCommandOptionType.ROLE,
                               required=True)
                       ])
    async def claim_role(self, ctx: SlashContext, role: discord.Role):
        await ctx.defer()
        check_user_exists(self.bot.db, ctx.author)
        self.bot.db.execute("UPDATE UserData SET role_id = ? WHERE id = ?", (role.id, ctx.author_id))
        embed = discord.Embed(title="Role Claimed",
                              description=f"You have claimed {role.mention} as your colour role",
                              colour=role.colour)
        await ctx.send(embed=embed, hidden=True)


    @cog_ext.cog_slash(name="reset_db",
                       description="[ADMIN] Reset Database)",
                       guild_ids=[336950154189864961])
    async def reset_db(self, ctx: SlashContext):
        await ctx.defer()
        if ctx.author == self.bot.me:
            confirmation_message = ConfirmationMessage(self.bot, ctx,
                                                       content="Are you sure you would like to reset the Database?")
            if confirmation_message.get_response():
                self.bot.db.execute("DROP TABLE UserData")
                await ctx.send(":warning: Database reset!")
                self.bot.db.execute("""CREATE TABLE IF NOT EXISTS UserData (
                                                    id INT NOT NULL PRIMARY KEY,
                                                    money INT,
                                                    role_id INT DEFAULT NULL)""")
        else:
            await ctx.send("You do not have the permissions to use this command")


def get_valid_hex(string: str):
    result = re.match(r"^#?[0-9a-fA-F]{6}$", string)
    if result:
        sixteen_int_hex = int("0x" + result.group().replace("#", ""), 16)
        return int(hex(sixteen_int_hex), 0)
    else:
        return None


def check_user_exists(db, user: discord.User) -> int:
    results = db.get("SELECT * FROM UserData WHERE id = ?", (user.id,))
    if len(results) == 0:
        enlist_user(db, user)
    return user.id


def enlist_user(db, user: discord.User):
    db.execute("INSERT INTO UserData VALUES (?, 100, NULL)", (user.id,))


class Timer:
    def __init__(self, operation_str: str):
        self.operation_str = operation_str
        self.start_time = None


    def __enter__(self):
        self.start_time = datetime.datetime.now()


    def __exit__(self, exc_type, exc_val, exc_tb):
        total_time = datetime.datetime.now() - self.start_time
        print(f"{self.operation_str} completed in {total_time.seconds}.{str(total_time.microseconds)[:3]} seconds!")



class Button:
    def __init__(self,
                 style: ButtonStyle = 2,
                 label: str = "",
                 emoji = None,
                 custom_id: str = None,
                 url: str = None,
                 disabled: bool = False):
        self.style = style
        self.label = label
        self.emoji = emoji
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled


class InteractiveMessage:
    def __init__(self, bot: discord.Client, content: str = "", embed: discord.Embed = None):
        self.bot = bot
        self.content = content
        self.embed = embed
        self.comps = [[] for i in range(5)]
        self.callbacks = {}
        self.timeout = None

        self.Callback = namedtuple("callback", "func args kwargs")


    def add_button(self, row: int, button: Button, callback: callable = None, *args, **kwargs,):
        if callback:
            self.callbacks[button.custom_id] = self.Callback(callback, args, kwargs)
        if button.url and button.style != ButtonStyle.URL:
            raise AttributeError("URL button requires URL style")
        self.comps[row].append(create_button(
            style=button.style,
            label=button.label,
            disabled=button.disabled
        ))
        if button.custom_id:
            print(f"{button.custom_id=}")
            self.comps[row][-1]["emoji"] = button.custom_id
        if button.emoji:
            print(f"{button.emoji=}")
            self.comps[row][-1]["emoji"] = button.emoji
        if button.url:
            print(f"{button.url=}")
            self.comps[row][-1]["url"] = button.url
        print(self.comps[row][-1])


    def add_timeout(self, callback, *args, **kwargs):
        self.timeout = self.Callback(callback, args, kwargs)


    async def send_message(self, ctx: SlashContext):
        comps = [create_actionrow(*row) for row in self.comps if len(row) > 0]
        await ctx.send(self.content, embed=self.embed, components=comps)
        listening = True
        while listening:
            try:
                button_ctx: ComponentContext = await manage_components.wait_for_component(self.bot, components=self.comps)
                callback = self.callbacks[button_ctx.custom_id]
                await callback.func(button_ctx, *callback.args, **callback.kwargs)
            except asyncio.TimeoutError:
                if self.timeout:
                    self.timeout.callback(*self.timeout.args, **self.timeout.kwargs)


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
