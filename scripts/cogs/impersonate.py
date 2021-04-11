import discord
from discord.ext import commands
import random


RELATIONS = {}

CHANNEL_HISTORY = []

CHAT_LOGGED = False


class Impersonate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="impersonate",
                        aliases=["imp"],
                        description="Impersonate another user based on how they talk in this server")
    async def impersonate(self, ctx, user, sentences=1):
        channel = ctx.message.channel
        command_msg = await channel.fetch_message(channel.last_message_id)
        await command_msg.delete()
        if len(CHANNEL_HISTORY) > 0:
            target_id = int(user[3:-1])
            try:
                target = await self.bot.fetch_user(target_id)
            except discord.ext.commands.errors.CommandInvokeError:
                await ctx.send(f"{ctx.message.author.mention} The user you tagged, {user}, could not be found")
                return
            if target is None:
                await channel.send(f"{ctx.message.author.mention} Incorrect command format - usage is `$impersonate [mention user] [number of sentences]`", delete_after=5)
            if target.id not in RELATIONS:
                await build_relations(target, channel)
            word_objs = RELATIONS[target.id]["all_words"]
            generating_sentence = True

            message = ""
            generating_message = True
            for i in range(sentences):
                word = random.choice(RELATIONS[target.id]["starters"])
                message += word.string
                while generating_sentence:
                    word = word.get_next_word()
                    if word is None:
                        generating_sentence = False
                    else:
                        message += f" {word.string}"

                message += ". "
            await channel.send(f"**{target}:** {message}")
        else:
            await channel.send("The chat must be logged before you can generate messages", delete_after=5)
            await self.logchat(ctx)
            await self.impersonate(ctx, user, sentences)


    @commands.command(name="logchat")
    async def logchat(self, ctx, limit=50000):
        CHANNEL_HISTORY.clear()
        channel = ctx.message.channel
        await channel.send(f"Logged **[0/{limit}]** messages from **#{channel.name}**")
        logging_message = await channel.fetch_message(channel.last_message_id)
        count = 0

        async for message in channel.history(limit=limit):
            count += 1
            CHANNEL_HISTORY.append(message)
            if count % 2000 == 0:
                await logging_message.edit(
                    content=f"Logged **[{count}/{limit}]** messages from **#{channel.name}**")
        await channel.send("Logging complete :white_check_mark:", delete_after=5)
        await logging_message.delete()


async def build_relations(target, channel):
    await add_user_lists(target)
    await channel.send(f"Building word relation network from **{target}**'s messages, this may take a while...")
    target_messages = []
    print(f"Finding {target}'s messages")
    count = 0
    async with channel.typing():
        for message in CHANNEL_HISTORY:
            count += 1
            if message.author == target:
                target_messages.append(message.content)
        print(f"Found {len(target_messages)} messages authored by {target}")
        word_objs = generate_word_objs(target_messages)
        starters = []
        for message in target_messages:
            message_words = message.split(" ")
            for i, word in enumerate(message_words):
                if i < len(message_words) - 1:
                    next_word = get_word_obj(word_objs, message_words[i + 1])
                else:
                    next_word = None
                word_obj = get_word_obj(word_objs, word)
                word_obj.add_occurance(next_word)
                if i == 0:
                    word_obj.starts += 1
        print("Relational database generated")
        for word in word_objs:
            if word.starts > 0:
                starters.append(word)
        print(RELATIONS)
        RELATIONS[target.id]["all_words"].extend(word_objs)
        RELATIONS[target.id]["starters"].extend(starters)


async def add_user_lists(user):
    if user.id not in RELATIONS:
        RELATIONS[user.id] = {}
    if "all_words" not in RELATIONS[user.id]:
        RELATIONS[user.id]["all_words"] = []
    if "starters" not in RELATIONS[user.id]:
        RELATIONS[user.id]["starters"] = []
    print(RELATIONS[user.id])


def generate_word_objs(message_data):
    word_objs = []
    all_words = [word for message in message_data for word in message.split(" ")]
    for word in all_words:
        if word not in [word_obj.string for word_obj in word_objs]:
            word_objs.append(Word(word))
    return word_objs


def get_word_obj(words_list, target_string):
    for word_obj in words_list:
        if word_obj.string == target_string:
            return word_obj


class Word:
    def __init__(self, string):
        self.string = string
        self.starts = 0
        self.following_words = {"END": 0}

    def __hash__(self):
        return hash(self.string)

    def __eq__(self, other):
        return self.string == other.string

    def __str__(self):
        return self.string

    def add_occurance(self, word):
        if word is None:
            self.following_words["END"] += 1
            return
        if word not in self.following_words:
            self.following_words[word] = 0
        self.following_words[word] += 1

    def get_next_word(self):
        next_word = random.choice([word for word in self.following_words for y in range(self.following_words[word])])
        if isinstance(next_word, str):
            return None
        return next_word



def setup(bot):
    bot.add_cog(Impersonate(bot))
