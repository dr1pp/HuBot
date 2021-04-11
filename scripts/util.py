import asyncio

from discord.ext import commands
from discord.ext.commands import Bot


async def get_last_message(channel):
    return await channel.fetch_message(channel.last_message_id)


async def send_timed(channel, content, timeout=5):
    await channel.send(content)
    message = await get_last_message(channel)
    await asyncio.sleep(timeout)
    await message.delete()