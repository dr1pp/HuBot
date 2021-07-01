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
            if len(results) > 0:
                role_id = results[0][0]
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                await role.edit(colour=discord.Colour(hex_string))
                embed = discord.Embed(title="Colour Set",
                                      description=f"Colour of {role.mention} set as {colour}",
                                      colour=role.colour)
                await ctx.send(embed=embed)
            else:
                await ctx.send("You need to claim your role using /claim_role before you can change your colour!",
                               hidden=True)
                return
        else:
            await ctx.send(f"'{colour}' is not a valid hex string")


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


# TODO : Create member class to replace current economy system to be more object oriented
#        Possibly with a decorator for commands which automatically creates the Member object


class Timer:
    def __init__(self, operation_str: str):
        self.operation_str = operation_str
        self.start_time = None


    def __enter__(self):
        self.start_time = datetime.datetime.now()


    def __exit__(self, exc_type, exc_val, exc_tb):
        total_time = datetime.datetime.now() - self.start_time
        print(f"{self.operation_str} completed in {total_time.seconds}.{str(total_time.microseconds)[:3]} seconds!")


class Callback:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.ctx = None

    async def call(self, ctx):
        await self.func(ctx, *self.args, **self.kwargs)


class Button:
    def __init__(self,
                 row: int = 0,
                 style: ButtonStyle = 2,
                 label: str = "",
                 emoji = None,
                 custom_id: str = None,
                 url: str = None,
                 disabled: bool = False,
                 callback: Callback = None
                 ):
        self.row = row
        self.style = style
        self.label = label
        self.emoji = emoji
        self.custom_id = custom_id
        self.url = url
        if self.url and self.style != ButtonStyle.URL:
            raise AttributeError("URL button requires URL style")
        self.disabled = disabled
        self.callback = callback
        self.button = self.get_button_dict()


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.custom_id == other.custom_id
        elif isinstance(other, str):
            return self.custom_id == other
        else:
            return False


    def get_button_dict(self):
        button = create_button(
            style=self.style,
            label=self.label,
            disabled=self.disabled
        )
        if not self.custom_id:
            self.custom_id = self.label.lower()
        button["custom_id"] = self.custom_id
        if self.emoji:
            button["emoji"] = self.emoji
        if self.url:
            button["url"] = self.url
        return button


    def update_attribute(self, attribute: str, value):
        self.button[attribute] = value


class InteractiveMessage:
    """
    Dynamic slash command message using buttons for user interaction.
    ...

    Attributes
    ----------
        ctx:
            the message context
        bot: (commands.Bot)
            the bot sending the message
        content: str, optional
            the text body of the message
        embed: discord.Embed, optional
            the message embed

    Methods
    -------
        add_button(button):
            Adds a button to the objects list of buttons
        add_timeout(time, callback, *args, **kwargs):
            Adds a function to be called if the user does not interact with the message in a set amount of time
        get_action_rows():
            Returns a list of action_rows containing all of the Button dictionaries ready to be sent in a message
        send_message():
            Sends the interactive message to the discord.Messagable specified by the given context object
        update_message():
            Updates the message to represent the current state of the InteractiveMessage object
    """

    def __init__(self, ctx, bot: commands.Bot, content: str = "", embed: discord.Embed = None):
        self.ctx = ctx
        self.bot = bot
        self.content = content
        self.embed = embed
        self.buttons = list()
        self.comps = [{} for i in range(5)]
        self.timeout = 30
        self.timeout_callback = None


    def add_button(self, button: Button):
        self.buttons.append(button)


    def add_timeout(self, time: int, callback, *args, **kwargs):
        self.timeout = time
        self.timeout_callback = Callback(callback, args, kwargs)


    def get_action_rows(self):
        rows = [[] for i in range(5)]
        for button in self.buttons:
            if len(rows[button.row]) <= 5:
                rows[button.row].append(button.get_button_dict())
            else:
                raise IndexError("Action Rows can contain between 1 and 5 components!")
        return [create_actionrow(*[comp for comp in row]) for row in rows if len(row) > 0]


    async def send_message(self):
        print(self.embed)
        await self.ctx.send(self.content, embed=self.embed, components=self.get_action_rows())
        listening = True
        while listening:
            try:
                button_ctx: ComponentContext = await manage_components.wait_for_component(self.bot,
                                                                                          components=self.get_action_rows(),
                                                                                          timeout=self.timeout)
                callback = [button.callback for button in self.buttons if button.custom_id == button_ctx.custom_id][0]
                await callback.call(button_ctx)
            except asyncio.TimeoutError:
                if self.timeout_callback:
                    self.timeout_callback.call()


    async def update_message(self):
        await self.ctx.message.edit(content=self.content, embed=self.embed, components=self.get_action_rows())


class ConfirmationMessage(InteractiveMessage):
    def __init__(self, bot, ctx, content: str, timeout: int = 15):
        super().__init__(ctx, bot, content)
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
