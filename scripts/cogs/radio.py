import discord
import random as rand
import spotipy as sp
import youtube_dl
import os

from spotipy.oauth2 import  SpotifyClientCredentials
from discord.ext import commands
from youtube_search import YoutubeSearch

PLAYLIST_ID = "0EhIVTYDVaurXWRIXqB9At"

spotify = sp.Spotify(client_credentials_manager=SpotifyClientCredentials())

ydl_ops = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="join")
    async def join(self, ctx):
        self.channel = ctx.guild.get_channel(838175571216564264)
        self.voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not self.voice:
            self.voice = await self.channel.connect()

        elif not self.voice.is_connected():
            await self.channel.connect()
        else:
            await self.voice.move_to(self.channel)

        first = await get_random_search_term()
        await self.play_track(first)


    async def play_track(self, track):
        url = f"https://www.youtube.com{YoutubeSearch(track, max_results=1).to_dict()[0]['url_suffix']}"

        with youtube_dl.YoutubeDL(ydl_ops) as ydl:
            ydl.download([url])

        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3")
        next = await get_random_search_term()
        self.voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: await self.play_track(next))
        await self.channel.edit(name=f"{track}")


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


    @commands.command(name="random")
    async def random(self, ctx):
        name = await get_random_search_term()
        await ctx.send(name)





async def get_random_search_term():
    total_tracks = int(spotify.playlist(PLAYLIST_ID)['tracks']['total'])

    tracks = []
    while len(tracks) < total_tracks:
        results = spotify.playlist_items(PLAYLIST_ID, limit=100, offset=len(tracks))
        tracks.extend(results["items"])

    track_names = [f"{track['track']['album']['artists'][0]['name']} - {track['track']['name']}" for track in
                   tracks]
    return rand.choice(track_names)


def setup(bot):
    bot.add_cog(Radio(bot))
