import discord
from discord.ext.commands import Bot
import os
#from dataclasses import dataclass, field

client = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game("Work In Progress"))

@client.command()
async def ping(ctx):
    await ctx.send("Pong")


client.run(TOKEN)