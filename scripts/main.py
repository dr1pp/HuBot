import discord
import util
import os



from discord.ext.commands import Bot
from doppelganger import build_relations
from markov_chain import Word


#from dataclasses import dataclass, field


client = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game("Work In Progress"))

@client.command()
async def ping(ctx):
    await ctx.send("Pong")

@client.command(pass_context=True,
                name="imp")
async def imp(ctx, user, message_count):
    channel = ctx.channel
    cmd_msg = await util.get_last_message(channel)
    await cmd_msg.delete()




@client.group(pass_context=True,
              invoke_without_command=True,
              name="impersonate"
              )
async def impersonate(ctx, user, sentences=1):
    channel = ctx.message.channel
    command_msg = await util.get_last_message(channel)
    await command_msg.delete()
    if len(CHANNEL_HISTORY) > 0:
        target_id = int(user[3:-1])
        target = bot.get_user(target_id)
        if target is None:
            await util.send_timed(channel,
                                   f"{ctx.message.author.mention} Incorrect command format - usage is `$impersonate [mention user] [number of sentences]`")
        print("Building message")
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
        await util.send_timed(channel, "The chat must be logged before you can generate messages")



client.run(TOKEN)