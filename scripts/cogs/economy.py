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



class EconomyManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db


    def balance(self, user: discord.User):
        id = self.get_id(user)
        results = self.db.get("SELECT money FROM UserData WHERE id = ?", (id,))
        balance = int(results[0][0])
        return balance


    def get_id(self, user):
        if isinstance(user, discord.Member):
            print("user")
            id = user.id
        elif isinstance(user, int):
            print("int")
            id = user
        elif isinstance(user, str):
            print("string")
            id = int(user)
        else:
            print(type(user))
            id = None
        return id


    def enlist_user(self, id: int):
        self.db.execute("INSERT INTO UserData VALUES (?, 100)", (id,))
        print("enlisted", id)


    def check_user_exists(self, user: discord.User):
        id = self.get_id(user)
        results = self.db.get("SELECT * FROM UserData WHERE id = ?", (id,))
        if len(results) == 0:
            self.enlist_user(id)


    def give_money(self, user: discord.User, amount: int):
        id = self.get_id(user)
        current = self.balance(user)
        self.db.execute("UPDATE UserData SET money = ? WHERE id = ?", (current + amount, id))


    def can_afford(self, user: discord.User, amount: int):
        return self.balance(user) >= amount




def setup(bot):
    bot.add_cog(Economy(bot))
