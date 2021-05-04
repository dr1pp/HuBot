import discord
import random


from discord.ext import commands


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = self.bot.get_cog("Economy")
        self.econ_manager = self.economy.manager
        self.slots_mults = [
    {
        "mult": 0,
        "lower": 0,
        "upper": 7000,
        "emoji": ":no_entry_sign:"
    },
    {
        "mult": 1,
        "lower": 7000,
        "upper": 8000,
        "emoji": ":white_check_mark:"
    },
    {
        "mult": 2,
        "lower": 8000,
        "upper": 8700,
        "emoji": ":heavy_dollar_sign:"
    },
    {
        "mult": 5,
        "lower": 8700,
        "upper": 9300,
        "emoji": ":game_die:"
    },
    {
        "mult": 10,
        "lower": 9300,
        "upper": 9700,
        "emoji": ":bell:"
    },
    {
        "mult": 20,
        "lower": 9700,
        "upper": 9900,
        "emoji": ":cherries:"
    },
    {
        "mult": 50,
        "lower": 9900,
        "upper": 9999,
        "emoji": ":lemon:"
    },
    {
        "mult": 100,
        "lower": 9999,
        "upper": 10001,
        "emoji": ":seven:"
    }
]


    @commands.command(name="slots")
    async def slots(self, ctx, amount):
        user = ctx.message.author
        if amount == "all":
            amount = self.econ_manager.balance(user)
        elif amount == "half":
            amount = int(self.econ_manager.balance(user) / 2)
        else:
            amount = int(amount)
        if self.econ_manager.can_afford(user, amount):
            self.econ_manager.give_money(user, -amount)
            chance = random.randint(0, 10000)
            for m in self.slots_mults:
                if m["lower"] <= chance < m["upper"]:
                    winnings = amount * m["mult"]
                    self.econ_manager.give_money(user, winnings)
                    await ctx.reply(
                        f"| {m['emoji']} | {m['emoji']} | {m['emoji']} | `{chance}`\nYou got a **{m['mult']}x** multiplier and won **฿{winnings}**")
                    return
        else:
            await ctx.reply(f"{user.mention} You do not have enough to gamble")


def setup(bot):
    bot.add_cog(Games(bot))
