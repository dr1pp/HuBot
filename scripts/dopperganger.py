import discord
import asyncio
import time
import math
import random
import tools

from discord.ext import commands
from discord.ext.commands import Bot

RELATIONS = {}

CHANNEL_HISTORY = []

CHAT_LOGGED = False

@bot.event
async def on_ready():
    print("Bot Online")


@bot.command(pass_context=True,
             name="impersonate",
             aliases=["test"])
async def impersonate(ctx, user, sentences=1):



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


@bot.command(pass_context=True,
             name="logchat")
async def logchat(ctx, limit=50000):
    CHANNEL_HISTORY.clear()
    channel = ctx.message.channel
    await channel.send(f"Logged **[0/{limit}]** messages from **#{channel.name}**")
    logging_message = await tools.get_last_message(channel)
    count = 0

    async for message in channel.history(limit=limit):
        count += 1
        CHANNEL_HISTORY.append(message)
        if count % 2000 == 0:
            await logging_message.edit(content=f"Logged **[{count}/{limit}]** messages from **#{channel.name}**")
    await tools.send_timed(channel, "Logging complete :white_check_mark:")
    await logging_message.delete()


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


