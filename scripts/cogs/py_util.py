async def fetch_last_message(channel):
    await channel.fetch_message(channel.last_message_id)

