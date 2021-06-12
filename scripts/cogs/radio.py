import discord
import random as rand
import spotipy as sp
import youtube_dl
import os
import asyncio
import datetime
import cogs.utility as util

from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, create_choice
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from youtube_search import YoutubeSearch
from contextlib import suppress
from collections import namedtuple


INTERMISSIONS_DIR = "./radio_sounds"


PLAYLIST_ID = "0EhIVTYDVaurXWRIXqB9At"

ydl_ops = {
        'no_warnings': True,
        'format': 'bestaudio/best',
        'outtmpl': 'next.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128'
        }]
    }

spotify = sp.Spotify(client_credentials_manager=SpotifyClientCredentials())


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current = None
        self.channel = None
        self.playing = False
        print("[RADIO COG INIT] Creating initialization track")
        self.current = get_random_track()
        self.current.download()
        print("[RADIO COG INIT] Initialization track created")


    @cog_ext.cog_slash(name="join",
                       description="Summon the bot to play the radio in your current voice channel",
                       guild_ids=[336950154189864961],
                       options=[
                           create_option(
                               name="channel",
                               description="The voice channel for the bot to join",
                               option_type=SlashCommandOptionType.CHANNEL,
                               required=False
                           )
                       ])
    async def join(self, ctx: SlashContext, channel: discord.VoiceChannel = None):
        await ctx.defer()
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                self.channel = ctx.author.voice.channel
            else:
                self.channel = ctx.guild.get_channel(838175571216564264)
        else:
            if isinstance(channel, discord.VoiceChannel):
                self.channel = channel
            else:
                await ctx.send(f"{channel.mention} is not a voice channel", hidden=True)
                return

        print(f"[$JOIN] Target channel is {self.channel.name}")
        embed = discord.Embed(title="Discord FM :headphones:", colour=0x5DADEC)
        if voice := discord.utils.get(self.bot.voice_clients, guild=ctx.guild):
            self.voice = voice
            print(f"[$JOIN] Voice client connected to {self.voice.channel.name}")
            print(f"[$JOIN] Moving to {self.channel.name} per {ctx.author}'s request")
            await self.voice.move_to(self.channel)
            embed.add_field(name="**Moved to**", value=self.channel.mention)
            await ctx.send(embed=embed)
        else:
            print("[$JOIN] No voice client found in server, creating one")
            print(f"[$JOIN] Joining {self.channel.name} per {ctx.author}'s request")
            self.voice = await self.channel.connect()
            if not self.voice.is_connected():
                await self.channel.connect()
            embed.add_field(name="**Joined**", value=self.channel.mention)
            await ctx.send(embed=embed)
            self.playing = True
            await self.current.play(self.voice)


    @cog_ext.cog_slash(name="skip",
                       description="Skip the current song playing on the radio",
                       guild_ids=[336950154189864961])
    async def skip(self, ctx: SlashContext):
        await ctx.send(f":track_next: Skipped **{self.current.readable_name}**")
        await self.current.skip(self.voice)


    @cog_ext.cog_slash(name="disconnect",
                       description="Disconnect the bot from voice",
                       guild_ids=[336950154189864961])
    async def disconnect(self, ctx: SlashContext):
        await ctx.defer()
        if ctx.author.voice and ctx.author.voice.channel:
            if self.voice.is_connected():
                self.voice.stop()
                self.playing = False
                await self.voice.disconnect()
                await ctx.send(f":no_mobile_phones: Disconnected from **{self.voice.channel.mention}**")
                print("[DISCONNECT] Bot disconnected from voice")
            else:
                await ctx.send(":face_with_raised_eyebrow: The bot is not connected to a voice channel", hidden=True)


    @cog_ext.cog_slash(name="playlist",
                       description="Get a link to the playlist used for the radio station",
                       guild_ids=[336950154189864961])
    async def playlist(self, ctx: SlashContext):
        await ctx.send(f"https://open.spotify.com/playlist/{PLAYLIST_ID}", hidden=True)


    @cog_ext.cog_slash(name="np",
                       description="Show the song currently playing on the radio")
    async def now_playing(self, ctx: SlashContext):
        await ctx.defer()
        sent = False
        while not sent:
            try:
                embed = discord.Embed(title=f"{self.current.readable_name} 🎵",
                                      url=self.current.urls.spotify,
                                      description=f"<:youtube:847561221514985502> [Source]({self.current.urls.youtube})",
                                      colour=discord.Colour(0x1DB954))
                embed.set_thumbnail(url=self.current.urls.cover)
                embed.set_footer(text=f"Added by: {self.current.info.added_by.name}", icon_url=self.current.info.added_by.image_url)
                embed.add_field(name="Length",
                                value=self.current.info.duration, inline=True)
                embed.add_field(name="Progress", value=self.current.playing_progress(), inline=True)
                embed.add_field(name="In", value=self.voice.channel.name, inline=False)
                embed.add_field(name="Up Next",
                                value=f"[{self.current.next.readable_name}]({self.current.next.urls.spotify})",
                                inline=False)
                await ctx.send(embed=embed, hidden=True)
                sent = True
            except AttributeError:
                pass


class Track:

    Info = namedtuple("Info", "title artist duration duration_s added_by")
    Media = namedtuple("Media", "spotify youtube cover")

    def __init__(self, track_data):
        self.data = track_data['track']
        with util.Timer(f"[TRACK INIT] Initialisation of '{self.data['name']}'"):

            self.readable_name = f"{self.data['album']['artists'][0]['name']} - {self.data['name']}"

            with util.Timer(f"[TRACK INIT] YouTube data extraction for '{self.data['name']}'"):
                self.youtube_data = YoutubeSearch(self.readable_name, max_results=1).to_dict()[0]

            with util.Timer(f"[TRACK INIT] Spotify data extraction for '{self.data['name']}'"):
                self.info = self.Info(self.data['name'],
                                      self.data['album']['artists'][0]['name'],
                                      self.youtube_data['duration'],
                                      self.readable_time_to_seconds(self.youtube_data['duration']),
                                      SpotifyUser(spotify.user(track_data['added_by']['id'])))

            self.urls = self.Media(self.data['external_urls']['spotify'],
                                   f"https://www.youtube.com{self.youtube_data['url_suffix']}",
                                   self.data['album']['images'][1]['url'])


            self.readable_duration = self.info.duration
            if len(self.readable_duration) % 2 == 0 and not self.readable_duration.startswith("0"):
                self.readable_duration = "0" + self.readable_duration
            self.next = None
            self.is_downloaded = False
            self.started_playing_at = None
            self.skipped = False
            self.next = None


    async def play(self, voice):
        self.next = get_random_track()
        os.rename("next.mp3", "song.mp3")
        voice.play(discord.FFmpegPCMAudio("song.mp3"))
        self.started_playing_at = datetime.datetime.now()
        print(f"[PLAY_TRACK] Now playing '{self.readable_name}'")
        self.next.download()
        await asyncio.sleep(self.info.duration_s)
        if not self.skipped:
            os.remove("song.mp3")
            print(f"[PLAY_TRACK] Deleted song.mp3 for '{self.readable_name}'")
            await self.play_intermission(voice)
            await self.next.play(voice)


    async def skip(self, voice):
        voice.stop()
        self.skipped = True
        self.next.play(voice, get_random_track())


    async def play_intermission(self, voice):

        def get_intermission():
            if rand.randint(0,5) == 0:
                return rand.choice(os.listdir(INTERMISSIONS_DIR))
            return None

        if intermission := get_intermission():
            print(f"[PLAY_TRACK] Playing intermission '{intermission}'")
            voice.play(discord.FFmpegPCMAudio(f"{INTERMISSIONS_DIR}/{intermission}"))


    def download(self) -> datetime.timedelta:
        start_time = datetime.datetime.now()
        print(f"[YTDL] Attempting to download '{self.readable_name}' from {self.urls.youtube}")
        with youtube_dl.YoutubeDL(ydl_ops) as ydl:
            try:
                with util.Timer(f"[YTDL] Download of '{self.readable_name}'"):
                    with suppress(NotADirectoryError):
                        ydl.download([self.urls.youtube])
                self.is_downloaded = True
            except youtube_dl.utils.DownloadError as err:
                print(f"[YTDL] Download of '{self.readable_name}' threw the following exception: {err.exc_info[1]}")
                self.is_downloaded = False
            return datetime.datetime.now() - start_time


    def readable_time_to_seconds(self, time_string: str) -> int:
        (m, s) = map(int, time_string.split(":"))
        return (m * 60) + s


    def playing_progress(self) -> str:
        progress = datetime.datetime.now() - self.started_playing_at
        seconds = progress.seconds
        return f"{(seconds // 60):02d}:{(seconds % 60):02d}"


class SpotifyUser:

    def __init__(self, user_info):
        self.info = user_info
        self.name = self.info['display_name']
        self.image_url = self.info['images'][0]['url']


def get_random_track() -> Track:
    tracks = []
    total_tracks = int(spotify.playlist(PLAYLIST_ID)['tracks']['total'])
    while len(tracks) < total_tracks:
        results = spotify.playlist_items(PLAYLIST_ID, limit=100, offset=len(tracks))
        tracks.extend(results["items"])
    track_data = rand.choice(tracks)
    return Track(track_data)


def setup(bot):
    bot.add_cog(Radio(bot))
