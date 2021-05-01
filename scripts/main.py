import os
import datetime

from discord.ext.commands import Bot

# Add cogs to this list as they are merged into main branch
initial_extensions = ["cogs.radio"]


bot = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")

# Loads extensions (cogs) in from list provided
if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)

# Messages me on Discord when the bot is ready (faster than checking logs or typing a command)
@bot.event
async def on_ready():
    me = await bot.fetch_user(210454616876253184)
    await me.send(f"[ ✅ Online ] - {datetime.datetime.now()}")


bot.run(TOKEN)
