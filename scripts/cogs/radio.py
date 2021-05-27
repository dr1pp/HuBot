import discord
import random as rand
import spotipy as sp
import youtube_dl
import os
import asyncio
import warnings
import datetime

from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from youtube_search import YoutubeSearch

warnings.filterwarnings("ignore")

INTERMISSIONS_DIR = "./radio_sounds"


PLAYLIST_ID = "0EhIVTYDVaurXWRIXqB9At"

ydl_ops = {
        'format': 'bestaudio/best',
        'outtmpl': 'next.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

spotify = sp.Spotify(client_credentials_manager=SpotifyClientCredentials())


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current = None
        print("CREATING INITIALISATION TRACK")
        self.next = get_random_track()
        self.next.download()
        print("INIT TRACK CREATED")


    @commands.command(name="join",
                      aliases=["play", "radio"])
    async def join(self, ctx):

        if "next.mp3" not in os.listdir("./"):
            print("[$JOIN] Creating initial track")
            self.next = get_random_track()
            async with ctx.channel.typing():
                self.next.download()

        if ctx.author.voice and ctx.author.voice.channel:
            self.channel = ctx.author.voice.channel
        else:
            self.channel = ctx.guild.get_channel(838175571216564264)
        print(f"[$JOIN] Target channel is {self.channel.name}")

        self.voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if self.voice:
            print(f"[$JOIN] Voice client connected to {self.voice.channel.name}")
            print(f"[$JOIN] Moving to {self.channel.name} per {ctx.author}'s request")
            await self.voice.move_to(self.channel)
        else:
            print("[$JOIN] No voice client found in server, creating one")
            print(f"[$JOIN] Joining {self.channel.name} per {ctx.author}'s request")
            self.voice = await self.channel.connect()
            if not self.voice.is_connected():
                await self.channel.connect()
            await self.play_track()


    async def play_track(self):

        if "song.mp3" in os.listdir("./"):
            os.remove("song.mp3")
            print(f"[PLAY_TRACK] Deleted song.mp3 for '{self.current.readable_name}'")
        os.rename("next.mp3", "song.mp3")
        self.current = self.next
        print(f"[PLAY_TRACK] Renamed file for '{self.current.readable_name}'")
        self.voice.play(discord.FFmpegPCMAudio("song.mp3"),
                        after=lambda e: asyncio.run_coroutine_threadsafe(self.play_intermission(), self.bot.loop))
        self.current.started_playing_at = datetime.datetime.now()
        print(f"[PLAY_TRACK] Now playing '{self.current.readable_name}'")
        self.next = get_random_track()
        next_track_downloaded = False
        while not next_track_downloaded:
            if self.next.download():
                next_track_downloaded = True
            else:
                print(f"[PLAY_TRACK] Download of '{self.next.readable_name}' failed, attempting to download new track")
                self.next = get_random_track()
        return


    async def play_intermission(self):
        def get_intermission():
            names = os.listdir(INTERMISSIONS_DIR)
            if rand.randint(0, 5) == 0:
                return rand.choice(names)
            return None


        intermission = get_intermission()
        if intermission:
            print(f"[PLAY_TRACK] Playing intermission '{intermission}'")
            self.voice.play(discord.FFmpegPCMAudio(f"{INTERMISSIONS_DIR}/{intermission}"),
                            after=lambda e: asyncio.run_coroutine_threadsafe(self.play_track(), self.bot.loop))
        else:
            await self.play_track()


    @commands.command(name="skip",
                      aliases=["s", "kip"])
    async def skip(self, ctx):
        self.voice.stop()
        if not self.next.is_downloaded:
            self.next.download()
        await self.play_track()


    @commands.command(name="disconnect",
                      aliases=["dc", "leave"])
    async def disconnect(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            if self.voice.is_connected():
                self.voice.stop()
                await self.voice.disconnect()
                self.next = get_random_track()
            else:
                await ctx.send("The bot is not connected to a voice channel")


    @commands.command(name="playlist")
    async def playlist(self, ctx):
        await ctx.send(f"https://open.spotify.com/playlist/{PLAYLIST_ID}")


    @commands.command(name="nowplaying",
                      aliases=["np", "current", "next", ])
    async def now_playing(self, ctx):
        searching_message_sent = False
        sent = False
        while not sent:
            try:
                embed = discord.Embed(title=f"{self.current.readable_name} 🎵",
                                      url=self.current.youtube_url,
                                      description=f"[Spotify Link]({self.current.spotify_url})",  # TODO: Add youtube logo emoji and swap links (youtube link will say "Source"
                                      colour=discord.Colour(0x1DB954))
                embed.set_thumbnail(url=self.current.album_cover_url)
                embed.set_footer(text=f"Added by: {self.current.added_by.name}", icon_url=self.current.added_by.image_url)
                embed.add_field(name="Length", value=self.current.duration, inline=True)  # TODO: Pull duration from mp3 file rather than spotify
                embed.add_field(name="Progress", value=self.current.playing_progress(), inline=True)
                embed.add_field(name="In", value=self.voice.channel.name, inline=False)
                embed.add_field(name="Up Next", value=f"[{self.next.readable_name}]({self.next.spotify_url})", inline=False)  # TODO: Add time remaining to embed
                await ctx.send(embed=embed)
                sent = True
                if searching_message_sent:
                    await searching_message.delete()
            except AttributeError:
                if not searching_message_sent:
                    searching_message = await ctx.reply("🔎 Searching for song data, please wait...")
                    searching_message_sent = True
                with ctx.typing():
                    await asyncio.sleep(3)


class Track:

    def __init__(self, track_data):
        self.data = track_data
        self.title = self.data['track']['name']
        self.artist = self.data['track']['album']['artists'][0]['name']
        self.readable_name = f"{self.artist} - {self.title}"
        self.spotify_url = self.data['track']['external_urls']['spotify']
        start = datetime.datetime.now()
        self.youtube_data = YoutubeSearch(self.readable_name, max_results=1).to_dict()[0]
        print(f"[TRACK INIT] Found YouTube data for '{self.readable_name}' in {datetime.datetime.now() - start}s")
        self.youtube_url = f"https://www.youtube.com{self.youtube_data['url_suffix']}"
        self.duration = self.youtube_data['duration']
        self.album_cover_url = self.data['track']['album']['images'][1]['url']
        start = datetime.datetime.now()
        self.added_by = SpotifyUser(spotify.user(self.data['added_by']['id']))
        self.is_downloaded = False
        self.started_playing_at = None
        print(f"[TRACK INIT] Found Spotify Data for '{self.added_by.name}' in {datetime.datetime.now() - start}")
        print("[TRACK INIT] Initialisation complete!")


    def download(self) -> bool:
        start_time = datetime.datetime.now()
        print(f"[YTDL] Attempting to download '{self.readable_name}' from {self.youtube_url}")
        with youtube_dl.YoutubeDL(ydl_ops) as ydl:
            try:
                ydl.download([self.youtube_url])
                print(f"[YTDL] Download of '{self.readable_name}' complete in {datetime.datetime.now() - start_time}s!")
                self.is_downloaded = True
            except youtube_dl.utils.DownloadError as err:
                print(f"[YTDL] Download of $'{self.readable_name}' threw the following exception: {err.exc_info[1]}")
                self.is_downloaded = False
            return self.is_downloaded


    def playing_progress(self):
        progress = datetime.datetime.now() - self.started_playing_at
        seconds = progress.seconds
        return f"{(seconds // 60):02d}:{(seconds % 60):02d}"


class SpotifyUser:

    def __init__(self, user_info):
        self.info = user_info
        self.name = self.info['display_name']
        self.image_url = self.info['images'][0]['url']


def get_random_track():
    tracks = []
    total_tracks = int(spotify.playlist(PLAYLIST_ID)['tracks']['total'])
    while len(tracks) < total_tracks:
        results = spotify.playlist_items(PLAYLIST_ID, limit=100, offset=len(tracks))
        tracks.extend(results["items"])
    track_data = rand.choice(tracks)
    return Track(track_data)


def setup(bot):
    bot.add_cog(Radio(bot))
