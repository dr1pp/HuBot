import discord
import random
import asyncio
import datetime
import utility as util
import discord_components as components


from discord.ext import commands


CARD_NAMES = [
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Jack",
    "Queen",
    "King"
]

SUIT_NAMES = {
    "c": "Clubs",
    "h": "Hearts",
    "d": "Diamonds",
    "s": "Spades"
}


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


    @commands.command("blackjack")
    async def blackjack(self, ctx, minimum: int = 10):
        if minimum >= 10:
            blackjack = BlackJack(ctx, self.bot, minimum)
            await blackjack.play()
        else:
            await ctx.reply("Minimum bet must be at least 10")


    def get_card_string(self, name):
        for card in self.bot.playing_cards:
            if card.name == name:
                return
        return None


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
        self.wheel = []
        self.build_wheel()


    def build_wheel(self):
        for symbol in self.values.keys():
            symbols_list = [symbol] * int(10000 / (self.values[symbol]**2))
            self.wheel.extend(symbols_list)


    async def play(self):

        async def spin(ctx):
            if self.econ.can_afford(self.user, self.bet):
                await asyncio.sleep(4)
                self.econ.give_money(self.user, -self.bet)
                grid = self.generate_grid()
                won, mult = self.check_win(grid)
                winnings = int(self.bet * mult)
                self.econ.give_money(self.user, winnings)
                await ctx.respond(type=components.InteractionType.UpdateMessage,
                                  embed=self.build_embed(grid, won, mult))
            else:
                await ctx.respond(type=components.InteractionType.ChannelMessageWithSource,
                                  content=f"You cannot afford to put **฿{self.bet}** into this machine")
                await asyncio.sleep(5)
                await ctx.message.delete()


        async def quit(ctx):
            await ctx.message.delete()


        if self.econ.can_afford(self.user, self.bet):
            self.econ.give_money(self.user, -self.bet)
            grid = self.generate_grid()
            won, mult = self.check_win(grid)
            winnings = int(self.bet * mult)
            game = util.InteractiveMessage(self.bot, embed=self.build_embed(grid, won, mult))
            game.add_button(0, components.Button(label="Spin", style=components.ButtonStyle.green), spin)
            game.add_button(0, components.Button(label="Quit", style=components.ButtonStyle.red), quit)
            game.add_timeout(quit)
            self.econ.give_money(self.user, winnings)
            await game.send_message(self.ctx.channel)

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

class BlackJack:

    class Player:
        def __init__(self, bot: commands.Bot, user: discord.User, bet: int):
            self.bot = bot
            self.user = user
            self.bet = bet
            self.cards = list()
            self.stood = False
            self.played = False
            self.playing = True


        def give_random_cards(self, count: int=1):
            self.cards.extend(random.choice(self.bot.playing_cards) for i in range(count))


        def get_cards_string(self) -> str:
            cards_string = ""
            for card in self.cards:
                cards_string += str(card)
            return cards_string


        def get_cards_values(self) -> list:
            card_values = list()
            min_value = 0
            for card in self.cards:
                if card.face_up:
                    min_value += min([card.value, 10])
            card_values.append(min_value)
            for card in self.cards:
                if card.value == 1 and card.face_up:
                    card_values.append(card_values[-1] + 10)
            return card_values


        def get_best_card_total(self) -> int:
            best = 0
            for value in self.get_cards_values():
                if best < value < 22:
                    best = value
            return best


        def get_values_string(self) -> str:
            values = self.get_cards_values()
            values_string = str(values[0])
            if len(values) > 1:
                for value in values[1:]:
                    values_string += f"/{value}"
            return values_string


        def check_cards(self):
            if min(self.get_cards_values()) > 21:
                self.playing = False
                return False
            return True


        def can_play(self):
            return max(self.get_cards_values()) < 17


        def play(self):
            if self.can_play():
                self.give_random_cards()




    def __init__(self, ctx, bot, minimum: int=10):
        self.ctx = ctx
        self.bot = bot
        self.econ = self.bot.get_cog("Economy").manager
        self.minimum = minimum
        self.players = list()
        self.dealer = self.Player(self.bot, self.bot.user, 0)
        self.reactions = ("✅", "❌")



    async def play(self):

        async def take_bets():
            embed = self.build_betting_embed()
            betting_message = await self.ctx.send(embed=embed)
            num_bets = 0

            def check(m):
                if m.reference:
                    return m.reference.message_id == betting_message.id
                return False

            waiting = True
            while waiting:
                try:
                    msg = await self.bot.wait_for("message", timeout=10, check=check)
                    user = msg.author
                    try:
                        bet = int(msg.content)
                        if self.econ.can_afford(user, bet):
                            if bet >= self.minimum:
                                player = self.find_player(user)
                                if player is not None:
                                    player.bet += bet
                                else:
                                    self.players.append(self.Player(self.bot, user, bet))
                                await msg.delete()
                                await self.ctx.send(f"{user.mention} has placed a bet of **฿{bet}**")
                                num_bets += 1
                            else:
                                await self.ctx.reply(f"You must bet at least **฿{self.minimum}**")
                        else:
                            await self.ctx.reply("You do not have enough **e-฿ux** to bet this amount.")
                    except:
                        await self.ctx.send(f"'{msg.content}' is not a valid number")
                except asyncio.TimeoutError:
                    print("finished waiting")
                    waiting = False
            return num_bets


        async def round():

            async def initial_deal():
                self.dealer.give_random_cards(2)
                self.dealer.cards[1].flip()
                for player in self.players:
                    player.give_random_cards(2)
                embed = self.build_embed()
                msg = await self.ctx.send(embed=embed)
                for emoji in self.reactions:
                    await msg.add_reaction(emoji)
                return msg


            async def hit_cycle():
                for player in self.players:
                    player.played = False
                waiting = True
                while waiting:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=10)
                        player = self.find_player(user)
                        if player is not None:
                            if player.playing:
                                if reaction.emoji == "✅":
                                    if not player.stood:
                                        player.played = True
                                        player.give_random_cards()
                                elif reaction.emoji == "❌":
                                    print(f"{player.user} stood")
                                    player.stood = True
                                    player.played = True
                                    player.playing = False
                                await reaction.remove(user)
                                for player in self.players:
                                    if not player.played:
                                        print(f"{player.user} has not chosen")
                                        break
                                    print("All users have chosen")
                                    return
                            else:
                                await reaction.remove(user)
                        elif user != self.bot.user:
                            await reaction.remove(user)
                    except asyncio.TimeoutError:
                        for player in self.players:
                            if not player.played:
                                player.playing = False
                        waiting = False


            def check_finished():
                for player in self.players:
                    print(player.playing)
                    if player.playing:
                        print(f"{player.user} still playing")
                        break
                    print("All players finished playing")
                    return True


            async def give_winnings():
                msg = ""
                for player in self.players:
                    if player.get_best_card_total() > self.dealer.get_best_card_total():
                        msg += f"{player.user.mention} won **฿{player.bet}**\n"
                        self.econ.give_money(player.user, player.bet)
                    elif player.get_best_card_total() == self.dealer.get_best_card_total():
                        msg += f"{player.user.mention} Pushed\n"
                    elif player.get_best_card_total() < self.dealer.get_best_card_total():
                        msg += f"{player.user.mention} lost **฿{player.bet}**\n"
                        self.econ.give_money(player.user, -player.bet)
                    print(player.get_best_card_total(), self.dealer.get_best_card_total())
                await self.ctx.send(msg)


            finished = False
            game_msg = await initial_deal()
            self.dealer.cards[1].flip()
            await hit_cycle()
            await game_msg.edit(embed=self.build_embed())
            print("INITIAL HIT COMPLETE")
            finished = check_finished()
            while not finished:
                await hit_cycle()
                await game_msg.edit(embed=self.build_embed())
                finished = check_finished()
            if not check_finished():
                while self.dealer.can_play():
                    self.dealer.play()
            await asyncio.sleep(5)
            await game_msg.edit(embed=self.build_embed())
            await give_winnings()
            print("FINISHED")


        active = True
        while active:
            for player in self.players:
                player.bet = 0
            num_bets = await take_bets()
            if num_bets > 0:
                await round()
            else:
                active = False


    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"Blackjack - ฿{self.minimum} minimum", colour=0x038418)
        embed.add_field(name=f"Dealer - {self.dealer.get_values_string()}", value=self.dealer.get_cards_string(), inline=False)
        for player in self.players:
            min_value = min(player.get_cards_values())
            if min_value < 22:
                embed.add_field(name=f"{player.user} - **฿{player.bet}**",
                                value=f"{player.get_cards_string()}\n{player.get_values_string()}", inline=True)
            else:
                embed.add_field(name=f"~~{player.user} - **฿{player.bet}**~~ :boom:",
                                value=f"{player.get_cards_string()}\n{player.get_values_string()}", inline=True)
        return embed


    def build_betting_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"Blackjack - ฿{self.minimum} minimum",
                              description="Dealer must hit to 16, stand at 17\nStarts 10 seconds after final bet is placed",
                              colour=0x038418)
        embed.add_field(name="How to join:",
                        value="Reply to this message (Right click -> Reply) with the amount of **e-฿ux** you would like to bet on the game, then wait for it to start.",
                        inline=False)
        embed.add_field(name="How to play:",
                        value="Once the game has started, you will be dealt your cards. You can then either choose to Hit :white_check_mark: to recieve another card, or Stand :x: to finish with the hand you have.",
                        inline=False)
        return embed


    def find_player(self, user: discord.User):
        for player in self.players:
            if player.user.id == user.id:
                return player
        return None

class Card:
    def __init__(self, emoji):
        self.emoji = emoji
        self.id = self.emoji.id
        self.value = int(self.emoji.name[1:])
        self.suit = SUIT_NAMES[self.emoji.name[0]]
        self.name = CARD_NAMES[self.value-1]
        self.readable_name = f"{self.name} of {self.suit}"
        self.face_up = True


    def __str__(self):
        if self.face_up:
            return f"<:{self.emoji.name}:{self.id}>"
        else:
            return "<:card_back:840020324833165332>"


    def flip(self):
        self.face_up = not self.face_up


def setup(bot):
    bot.add_cog(Games(bot))
