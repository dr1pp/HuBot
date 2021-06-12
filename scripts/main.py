import os
import datetime
import warnings
from discord import Game, Embed
from discord_components import DiscordComponents
from discord_slash import SlashCommand


from discord.ext.commands import Bot
from sql import Database
from cogs.games import Card

init_time = datetime.datetime.now()

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
bot.db.initialize(["""CREATE TABLE IF NOT EXISTS UserData (
                                                    id INT NOT NULL PRIMARY KEY,
                                                    money INT,
                                                    role_id INT)"""])


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
    embed = Embed(title="Bot Online :white_check_mark:", colour=0x77B255)
    embed.add_field(name="Ready at", value=str(datetime.datetime.now()), inline=True)
    startup_time = datetime.datetime.now() - init_time
    embed.add_field(name="Startup Duration", value=f"{startup_time.seconds}.{str(startup_time.microseconds)[:3]} seconds")
    await bot.me.send(embed=embed)
    await bot.change_presence(activity=Game("$help"))


TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)
