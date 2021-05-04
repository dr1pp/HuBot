import os
import datetime
import warnings

import warnings

from discord.ext.commands import Bot
from sql import Database


warnings.filterwarnings("ignore")



warnings.filterwarnings("ignore")

# Add cogs to this list as they are merged into main branch
initial_extensions = ["cogs.economy",
                      "cogs.games",
                      "cogs.radio"]



bot = Bot(command_prefix="$")
bot.db = Database()
bot.db.execute("""CREATE TABLE IF NOT EXISTS UserData (
                                                    id INT NOT NULL PRIMARY KEY,
                                                    money INT)""")



# Loads extensions (cogs) in from list provided
if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)


# Messages me on Discord when the bot is ready (faster than checking logs or typing a command)
@bot.event
async def on_ready():
    print("===== [READY] =====")
    bot.me = await bot.fetch_user(210454616876253184)
    await bot.me.send(f"✅ Online - {datetime.datetime.now()}")
    print(bot.me)


TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)
