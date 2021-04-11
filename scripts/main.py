import os

from discord.ext.commands import Bot


initial_extensions = ["cogs.simple",
                      "cogs.impersonate"]


bot = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")


if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)


bot.run(TOKEN)
