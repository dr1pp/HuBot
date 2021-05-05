import discord
import random
import asyncio


from discord.ext import commands


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = self.bot.get_cog("Economy")
        self.econ_manager = self.economy.manager
        self.c4_pieces = [":yellow_circle:", ":red_circle:"]
        self.c4_emotes = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣']


    @commands.group(name="slots",
                    aliases=["slot", "lots", "lot"],
                    brief="Slot machine minigame")
    async def slots(self, ctx, amount=None):  # TODO : Refactor to use embed and be repeatable with current balance
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
        print(amount)
        if amount == "all":
            amount = self.econ_manager.balance(user)
        elif amount == "half":
            amount = int(self.econ_manager.balance(user) / 2)
        else:
            amount = int(amount)
        slots = SlotMachine(ctx, self.bot, amount)
        await slots.play()


    @slots.command("chances")
    async def chances(self, ctx):
        pass


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
                reaction, user = await self.bot.wait_for('reaction_add')  # TODO : Add forfeit option using red x reaction
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


class SlotMachine:
    def __init__(self, ctx, bot, bet: int):
        self.ctx = ctx
        self.bot = bot
        self.bet = bet
        self.user = self.ctx.message.author
        self.econ = self.bot.get_cog("Economy").manager
        self.values = {":watermelon:": 1,
                      ":apple:": 1,
                      ":tangerine:": 1.5,
                      ":lemon:": 2,
                      ":grapes:": 2.5,
                      ":cherries:": 3,
                      ":hearts:": 4,
                      ":four_leaf_clover:": 5,
                      ":euro:": 6,
                      ":dollar:": 7,
                      ":pound:": 8,
                      ":bell:": 10,
                      ":coin:": 20,
                      ":seven:": 50
                      }
        self.reactions = ["🔁", "❌"]
        self.wheel = []
        self.build_wheel()


    def build_wheel(self):
        for symbol in self.values.keys():
            symbols_list = [symbol] * int(10000 / (self.values[symbol]**2))
            self.wheel.extend(symbols_list)


    async def play(self):
        if self.econ.can_afford(self.user, self.bet):
            finished = False
            self.econ.give_money(self.user, -self.bet)
            grid = self.generate_grid()
            won, mult = self.check_win(grid)
            winnings = int(self.bet * mult)
            slot_message = await self.ctx.reply(embed = self.build_embed(grid, won, mult))
            self.econ.give_money(self.user, winnings)
            for reaction in self.reactions:
                await slot_message.add_reaction(reaction)
            while not finished:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30)
                    if user == self.user:
                        if reaction.emoji == "🔁":
                            await reaction.remove(user)
                            if self.econ.can_afford(self.user, self.bet):
                                await asyncio.sleep(4)
                                self.econ.give_money(self.user, -self.bet)
                                grid = self.generate_grid()
                                won, mult = self.check_win(grid)
                                winnings = int(self.bet*mult)
                                self.econ.give_money(self.user, winnings)
                                await slot_message.edit(embed=self.build_embed(grid, won, mult))
                            else:
                                broke_msg = await slot_message.reply(f"{self.user.mention} You cannot afford to put **฿{self.bet}** into this machine")
                                await asyncio.sleep(5)
                                await broke_msg.delete()
                                await slot_message.delete()
                                finished = True
                        elif reaction.emoji == "❌":
                            finished = True
                            await slot_message.delete()
                        else:
                            await reaction.remove(user)
                    else:
                        if user != self.bot.user:
                            await reaction.remove(user)
                except asyncio.TimeoutError:
                    finished = True
                    await slot_message.delete()
        else:
            await self.ctx.reply(f"You do not have enough **e-฿ux** to do that")



    def check_win(self, grid):
        for symbol in self.values.keys():
            num = grid[1].count(symbol)
            if num > 1:
                return True, num / 2
        return False, 0


    def generate_grid(self):
        grid = []
        for row in range(3):
            row = []
            for col in range(3):
                symbol = random.choice(self.wheel)
                row.extend([symbol])
            grid.append(row)
        return grid


    def build_embed(self, g, won, mult=0):
        embed = discord.Embed(title=f"Slot Machine - **฿{self.bet}**", description=f"Balance: **฿{self.econ.balance(self.user)}**")
        embed.add_field(name=":black_large_square::one:", value=f":blue_square: {g[0][0]}\n:arrow_right: {g[1][0]}\n:blue_square: {g[2][0]}")
        embed.add_field(name=":two:", value=f"{g[0][1]}\n{g[1][1]}\n{g[2][1]}")
        embed.add_field(name=":three::black_large_square:", value=f"{g[0][2]} :blue_square:\n{g[1][2]} :arrow_left:\n{g[2][2]} :blue_square:")
        if won is not None:
            if won:
                if mult == 1.0:
                    embed.add_field(name="__Results__",
                                    value=f"**{mult}x** multiplier\nBroke even")
                else:
                    embed.add_field(name="__Results__", value=f"**{mult}x** multiplier\nWon **฿{int(self.bet*mult)}**")
            else:
                embed.add_field(name="__Results__", value=f"No match\nLost **฿{int(self.bet)}**")
        return embed

def setup(bot):
    bot.add_cog(Games(bot))
