import discord
import sqlite3

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
        self.manager.check_user_exists(user)
        balance = self.manager.balance(user)
        embed = discord.Embed(title="Balance :credit_card:",
                              description=f"You have **฿{balance}** in your bank account",
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
                               choices=[
                                   create_choice(name="฿10", value=10),
                                   create_choice(name="฿100", value=100),
                                   create_choice(name="฿1,000", value=1000),
                                   create_choice(name="฿10,000", value=10000),
                                   create_choice(name="฿100,000", value=100000)
                               ]
                           )
                       ])
    async def gift(self, ctx, target: discord.User, amount: int):
        gifter = ctx.message.author
        if amount >= 1:
            if self.manager.can_afford(target, amount):
                self.manager.give_money(target, amount)
                self.manager.give_money(gifter, -amount)
                await ctx.reply(
                    f":money_with_wings: **฿{amount}** sent to **{target.mention}**")
            else:
                await ctx.reply(f":no_entry_sign: Your balance is too low to send **฿{amount}**")
        else:
            await ctx.reply("You must gift at least **฿1**")


class EconomyManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db


    def balance(self, user: discord.User):
        id = self.check_user_exists(user)
        results = self.db.get("SELECT money FROM UserData WHERE id = ?", (id,))
        balance = int(results[0][0])
        return balance


    def enlist_user(self, user: discord.User):
        self.db.execute("INSERT INTO UserData VALUES (?, 100)", (user.id,))


    def check_user_exists(self, user: discord.User):
        results = self.db.get("SELECT * FROM UserData WHERE id = ?", (user.id,))
        if len(results) == 0:
            self.enlist_user(user)
        return user.id


    def give_money(self, user: discord.User, amount: int):
        id = self.check_user_exists(user)
        current = self.balance(user)
        self.db.execute("UPDATE UserData SET money = ? WHERE id = ?", (current + amount, id))


    def can_afford(self, user: discord.User, amount: int):
        return self.balance(user) >= amount




def setup(bot):
    bot.add_cog(Economy(bot))
