import os

from discord.ext.commands import Bot


initial_extensions = ["cogs.simple",
                      "cogs.impersonate"]


client = Bot(command_prefix="$")
TOKEN = os.getenv("TOKEN")


if __name__ == "__main__":
    for extension in initial_extensions:
        client.load_extension(extension)


client.run(TOKEN)
