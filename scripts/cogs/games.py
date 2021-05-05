import discord
import random
import asyncio


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
        self.c4_pieces = [":large_blue_circle:", ":red_circle:"]
        self.c4_emotes = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣']


    @commands.group(name="slots")
    async def slots(self, ctx, amount=None):
        if amount is None:

            def check(m):
                if m.author == ctx.message.author:
                    try:
                        int(m.content)
                        return True
                    except:
                        return False
                else:
                    return False

            await ctx.reply(f"How many **e-฿UX** would you like to put in to the slot machine?")

            try:
                response = await self.bot.wait_for("message", timeout=20, check=check)
                amount = int(response.content)
                await ctx.invoke(self.slots.get_command('play'), amount=amount)

            except asyncio.TimeoutError:
                reply = await ctx.reply("You did not specify a wager amount")
                await asyncio.sleep(10)
                await reply.delete()
                await ctx.message.delete()

        elif amount == "chances":
            await ctx.invoke(self.slots.get_command('chances'))

        else:
            try:
                await ctx.invoke(self.slots.get_command('play'), amount=int(amount))
            except ValueError:
                await ctx.reply(f"`'{amount}'` is not a valid number of **e-฿UX**")


    @slots.command("play")
    async def play(self, ctx, amount):
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
            await ctx.reply(f"{user.mention} You do not have enough **e-฿UX** to bet **฿{amount}**")


    @slots.command("chances")
    async def chances(self, ctx):
        embed = discord.Embed(title="__Slot Machine Chances__")
        chance_names = ""
        chance_ranges = ""
        for chance in self.slots_mults:
            chance_names += f"{chance['emoji']} **{chance['mult']}x**\n"
            chance_ranges += f":game_die: **{chance['lower']} - {chance['upper']}**\n"
        embed.add_field(name="__Multiplier__", value=chance_names)
        embed.add_field(name="__Range__", value=chance_ranges)
        await ctx.reply(embed=embed)


    @commands.command(name="connect4",
                      aliases=["c4"])
    async def connect4(self, ctx, target: discord.User, wager: int = 0):

        turn = True


        def place_piece(board, turn, col):
            for row in reversed(board):
                if row[col] == ":black_circle:":
                    row[col] = self.c4_pieces[int(turn)]
                    return True, not turn, board


        def check_win(board):
            # Horizontal
            for y in range(0, 6):  # Rows
                for x in range(0, 4):  # Items in rows
                    if all_same(board[y][x:x + 4]) and board[y][x] != ":black_circle:":
                        return True

            # Vertical
            for y in range(0, 3):
                for x in range(0, 7):
                    vert = []
                    for i in range(0, 4):
                        vert.append(board[y + i][x])
                    if all_same(vert) and board[y][x] != ":black_circle:":
                        return True

            # Diag Right
            for y in range(0, 3):
                for x in range(0, 4):
                    diag = []
                    for i in range(0, 4):
                        diag.append(board[y + i][x + i])
                    if all_same(diag) and board[y][x] != ":black_circle:":
                        return True

            for y in range(0, 3):
                for x in range(3, 7):
                    diag = []
                    for i in range(0, 4):
                        diag.append(board[y + i][x - i])
                    if all_same(diag) and board[y][x] != ":black_circle:":
                        return True

            return False


        def all_same(items):
            return all(x == items[0] for x in items)


        def build_board_msg(board, won=False):
            if won:
                board_msg = f"**CONNECT 4:** `{players[0]} vs. {players[1]}`\n" \
                    f"**{self.c4_pieces[int(not turn)]} {players[int(not turn)]} won**\n" \
                    f":trophy: They will be recieving the **฿{wager * 2}** pot\n\n"
            else:
                board_msg = f"**CONNECT 4:** `{players[0]} vs. {players[1]}`\n" \
                    f"**{self.c4_pieces[int(turn)]} {players[int(turn)]}'s turn**\n" \
                    f":dollar: The pot contains **฿{wager * 2}**\n\n"
            board_msg += ":blue_square:"
            for emote in self.c4_emotes:
                board_msg += emote
            board_msg += ":blue_square:\n"
            for line in board:
                board_msg += ":blue_square:"
                for column in line:
                    board_msg += column
                board_msg += ":blue_square:\n"
            board_msg += ":blue_square:"
            for emote in self.c4_emotes:
                board_msg += emote
            board_msg += ":blue_square:"
            return board_msg


        author = ctx.message.author
        if not self.econ_manager.can_afford(target, wager) or not self.econ_manager.can_afford(author, wager):
            ctx.reply(f"Either one or both of the players do not have enough money to wager **฿{wager}**")
            return

        board = [[":black_circle:" for x in range(7)] for y in range(6)]
        players = [target, author]
        finished = False
        board_text = build_board_msg(board)
        message = await ctx.reply(board_text)
        for emote in self.c4_emotes:
            await message.add_reaction(emote)
        await asyncio.sleep(1)
        while not finished:
            won = False
            p1_turn = True
            while p1_turn:
                reaction, user = await self.bot.wait_for('reaction_add')
                if user == players[int(turn)] and reaction.emoji in self.c4_emotes:
                    column = int(reaction.emoji[0]) - 1
                    not_full, turn, board = place_piece(board, turn, column)
                    if not_full:
                        p1_turn = False
                    await reaction.remove(user)
                else:
                    await reaction.remove(user)

            won = check_win(board)
            if won:
                winner = players[int(not turn)]
                loser = players[int(turn)]
                await message.edit(content=build_board_msg(board, True))
                await message.clear_reactions()
                finished = True
                self.econ_manager.give_money(winner, wager * 2)
                self.econ_manager.give_money(loser, -wager)
            else:
                await message.edit(content=build_board_msg(board))


def setup(bot):
    bot.add_cog(Games(bot))
