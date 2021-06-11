import os
import datetime
import warnings
from discord import Game
from discord_components import DiscordComponents
from discord_slash import SlashCommand


from discord.ext.commands import Bot
from sql import Database
from cogs.games import Card


RED_CARDS_GUILD_ID = 839985921302069248
BLACK_CARDS_GUILD_ID = 839986047035506708


warnings.filterwarnings("ignore")


initial_extensions = ["cogs.utility",
                      "cogs.economy",
                      "cogs.games",
                      "cogs.radio"]



bot = Bot(command_prefix="$")
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)
bot.db = Database()
bot.db.execute("""CREATE TABLE IF NOT EXISTS UserData (
                                                    id INT NOT NULL PRIMARY KEY,
                                                    money INT,
                                                    role_id INT DEFAULT NULL)""")


if __name__ == "__main__":
    for extension in initial_extensions:
        bot.load_extension(extension)


# Messages me on Discord when the bot is ready (faster than checking logs or typing a command)
@bot.event
async def on_ready():
    DiscordComponents(bot)
    print("===== [READY] =====")
    bot.me = await bot.fetch_user(210454616876253184)
    emotes = await bot.get_guild(BLACK_CARDS_GUILD_ID).fetch_emojis()
    emotes.extend(await bot.get_guild(RED_CARDS_GUILD_ID).fetch_emojis())
    bot.playing_cards = [Card(emote) for emote in emotes if emote.name != "card_back"]
    await bot.me.send(f"✅ Online - {datetime.datetime.now()}")
    activity = Game("$help")
    await bot.change_presence(activity=activity)


TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)
