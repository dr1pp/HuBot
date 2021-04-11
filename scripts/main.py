import os
import datetime

from discord.ext.commands import Bot


initial_extensions = ["cogs.simple",
                      "cogs.impersonate"]


bot = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")


if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    me = await bot.fetch_user(210454616876253184)
    await me.send(f"✔️Online - {datetime.datetime.timestamp()}")


bot.run(TOKEN)
