import discord
import sqlite3

from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = EconomyManager(self.bot)

    @commands.command()
    async def balance(self, ctx):
        user = ctx.message.author
        self.manager.check_user_exists(user)
        balance = self.manager.balance(user)
        await ctx.reply(f":credit_card: You have **฿{balance}** in your bank account")


    @commands.command()
    async def givecash(self, ctx, target: discord.User, amount: int):
        if ctx.message.author == self.bot.me:
            self.manager.give_money(target, amount)
            await ctx.reply(f"**฿{amount}** given to {target.mention}")
        else:
            await ctx.reply(f"You cannot use this command")


    @commands.command()
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
        print("enlisted", user.id)


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
