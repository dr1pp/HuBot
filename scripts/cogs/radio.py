import discord
import random as rand
import spotipy as sp
import youtube_dl
import os
import asyncio
import warnings

from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from youtube_search import YoutubeSearch


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

warnings.filterwarnings("ignore")

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
        print("JOINING VOICE CHANNEL")

        async def play_track(track):
            print("PLAYING NEXT SONG")
            os.remove("song.mp3")
            os.rename("next.mp3", "song.mp3")
            self.current = track
            self.next = get_random_track()
            # self.voice.stop()  # Might be unnecessary
            await self.channel.edit(name=f"📻 {self.current.readable_name} 📻")
            self.voice.play(discord.FFmpegPCMAudio("song.mp3"),
                            after=lambda e: asyncio.run_coroutine_threadsafe(play_track(self.next), self.bot.loop))
            self.next.download()
            print("NEXT SONG DOWNLOADED")

        if "next.mp3" not in os.listdir("./"):
            print("CREATING TRACK AS NONE FOUND")
            self.next = get_random_track()
            async with ctx.channel.typing():
                self.next.download()

        self.channel = ctx.guild.get_channel(838175571216564264)
        await self.channel.edit(name="📻 DiscordFM 📻")
        self.voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not self.voice:
            self.voice = await self.channel.connect()

        elif not self.voice.is_connected():
            await self.channel.connect()
        else:
            await self.voice.move_to(self.channel)

        self.voice.stop()

        await play_track(self.next)


    @commands.command(name="disconnect",
                      aliases=["dc", "leave"])
    async def disconnect(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice.is_connected():
                await voice.disconnect()
            else:
                await ctx.send("The bot is not connected to a voice channel")


    @commands.command(name="playlist")
    async def playlist(self, ctx):
        await ctx.send(f"https://open.spotify.com/playlist/{PLAYLIST_ID}")


    @commands.command(name="nowplaying",
                      aliases=["np"])
    async def now_playing(self, ctx):
        embed = discord.Embed(title=f"{self.current.readable_name} 🎵",
                              url=self.current.youtube_url,
                              description=f"[Spotify Link]({self.current.spotify_url})",
                              colour=discord.Colour(0x2e7158))
        embed.set_thumbnail(url=self.current.album_cover_url)
        embed.set_footer(text=f"Added by: {self.current.added_by.name}", icon_url=self.current.added_by.image_url)
        embed.add_field(name="Length", value=self.current.duration, inline=True)                                        # TODO: Pull duration from mp3 file rather than spotify
        embed.add_field(name="Up Next", value=f"[{self.next.readable_name}]({self.next.spotify_url})", inline=False)    # TODO: Add time remaining to embed
        await ctx.send(embed=embed)


class Track:

    def __init__(self, track_data):
        self.data = track_data
        self.title = self.data['track']['name']
        self.artist = self.data['track']['album']['artists'][0]['name']
        self.readable_name = f"{self.artist} - {self.title}"
        self.spotify_url = self.data['track']['external_urls']['spotify']
        self.youtube_data = YoutubeSearch(self.readable_name, max_results=1).to_dict()[0]
        self.youtube_url = f"https://www.youtube.com{self.youtube_data['url_suffix']}"
        self.duration = self.youtube_data['duration']
        self.album_cover_url = self.data['track']['album']['images'][1]['url']
        self.added_by = SpotifyUser(spotify.user(self.data['added_by']['id']))


    def download(self):
        with youtube_dl.YoutubeDL(ydl_ops) as ydl:
            ydl.download([self.youtube_url])


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
