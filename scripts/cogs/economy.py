import discord
import sqlite3
import cogs.utility as util

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, create_choice


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = EconomyManager(self.bot)


    @cog_ext.cog_slash(name="balance",
                       description="Check your bank balance",
                       guild_ids=[336950154189864961])
    async def balance(self, ctx: SlashContext):
        user = ctx.author
        balance = self.manager.balance(user)
        embed = discord.Embed(title="Balance :credit_card:",
                              description=f"Your current balance is:\n**฿{balance}**",
                              colour=0xFEB242)
        await ctx.send(embed=embed, hidden=True)


    @cog_ext.cog_slash(name="givemoney",
                       description="[ADMIN] Give a user money",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(
                               name="user",
                               description="The user you would like to give money to",
                               option_type=SlashCommandOptionType.USER,
                               required=True
                           ),
                           create_option(
                               name="amount",
                               description="The amount of money you would like to give to the user",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True,
                               choices=[
                                   create_choice(name="฿10", value=10),
                                   create_choice(name="฿100", value=100),
                                   create_choice(name="฿1,000", value=1000),
                                   create_choice(name="฿10,000", value=10000),
                                   create_choice(name="฿100,000", value=100000)
                               ]
                           )
                       ])
    async def givemoney(self, ctx: SlashContext, user: discord.User, amount: int):
        if ctx.author == self.bot.me:
            self.manager.give_money(user, amount)
            await ctx.send(f":shushing_face: **฿{amount}** given to **{user.nick}**", hidden=True)
        else:
            await ctx.send(f":no_entry_sign: You cannot use this command.", hidden=True)


    @cog_ext.cog_slash(name="gift",
                       description="Gift another user some of your money",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(
                               name="target",
                               description="The user you would like to gift money to",
                               option_type=SlashCommandOptionType.USER,
                               required=True
                           ),
                           create_option(
                               name="amount",
                               description="The amount of money you would like to gift",
                               option_type=SlashCommandOptionType.INTEGER,
                               required=True,
                           )
                       ])
    async def gift(self, ctx: SlashContext, target: discord.User, amount: int):
        gifter = ctx.author
        if amount >= 1:
            if self.manager.can_afford(target, amount):
                self.manager.give_money(target, amount)
                self.manager.give_money(gifter, -amount)
                await ctx.send(
                    f":money_with_wings: **฿{amount}** sent to **{target.mention}**")
            else:
                await ctx.send(f":no_entry_sign: Your balance is too low to send **฿{amount}**", hidden=True)
        else:
            await ctx.send("You must gift at least **฿1**", hidden=True)


class EconomyManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db


    def balance(self, user: discord.User) -> int:
        user_id = util.check_user_exists(user)
        results = self.db.get("SELECT money FROM UserData WHERE id = ?", (user_id,))
        balance = int(results[0][0])
        return balance


    def give_money(self, user: discord.User, amount: int):
        user_id = util.check_user_exists(user)
        current = self.balance(user)
        self.db.execute("UPDATE UserData SET money = ? WHERE id = ?", (current + amount, user_id))


    def can_afford(self, user: discord.User, amount: int) -> bool:
        return self.balance(user) >= amount


def setup(bot):
    bot.add_cog(Economy(bot))
