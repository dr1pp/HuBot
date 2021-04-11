import asyncio

async def fetch_last_message(channel):
    await channel.fetch_message(channel.last_message_id)

async def send_timed(channel, content, timeout=5):
    await channel.send(content)
    message = await fetch_last_message(channel)
    await asyncio.sleep(timeout)
    await message.delete()

