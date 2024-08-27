import time
import asyncio
import os
import re
import urllib.request
import twitchio
import aiohttp

from datetime import datetime
from requests import get
from threading import Thread
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from twitchio.ext import commands
from twitchio.ext.commands.errors import CommandNotFound
from yt_dlp import YoutubeDL
from youtube_title_parse import get_artist_title

# TODO: Написать гайд по развертыванию бота из сурсов. Переписать все try/except с учетом ошибок.

load_dotenv()

sp = Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv('SP_CLIENT'),
        client_secret=os.getenv('SP_SECRET'),
        redirect_uri="http://localhost:8080",
        scope=[
            "user-modify-playback-state",
            "user-read-currently-playing",
            "user-read-playback-state",
            "user-read-recently-played",
        ],
    )
)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token = os.getenv('TW_OAUTH'),
            client_id = os.getenv('TW_CLIENT'),
            nick = os.getenv('BOT_NICK'),
            prefix = os.getenv('PREFIX'),
            timeout = 99,
            initial_channels = [os.getenv('STREAMER')],
            song_playing = "AAA - AAA",
            las = [],
            sk = 0,
        )
        
    async def event_ready(self):
        print(f"{self.nick} подключается к чату {self.initial_channels[0]}")

    @commands.command(name="np", aliases=["song"])
    async def np_command(self, ctx):
        try:
            artist = ', '.join([artist["name"] for artist in sp.currently_playing()["item"]["artists"]])
            track = data['item']['name']
            await ctx.send(f"@{ctx.author.name}, Сейчас играет {artist} - {track}")
        except:
            await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")

    @commands.command(name="sr", aliases=["p"])
    async def sr_command(self, ctx, *, song: str = None):
        if not song:
            await ctx.send(f"@{ctx.author.name}, Укажите название/ссылку на песню!")
            return
        song_uri = None
        if (
            song.startswith("spotify:track:") or islink(song) and not song.startswith("spotify:track:")):
            nss = song
            if "youtu" in song:
                try:
                    song = scrape_info(song)
                except:
                    song = nss
                await self.chat_sr(ctx, song, song_uri)
            else:
                song_uri = song
                await self.chat_sr(ctx, song, song)
        else:
            await self.chat_sr(ctx, song, song_uri)

    @commands.command(name="fskip")
    async def fskip_song_command(self, ctx):
        if ctx.author.is_mod:
            self.las = []
            self.sk = 0
            if sp.currently_playing():
                try:
                    sp.next_track()
                    await ctx.send(f"@{ctx.author.name}, Скипаем...")
                except:
                    await generate_response(ctx, "error")
            else:
                await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")
        else:
            await generate_response(ctx, "no_perm")

    @commands.command(name="pause")
    async def pause_song_command(self, ctx):
        if ctx.author.is_mod:
            try:
                sp.pause_playback()
                await ctx.send(f"@{ctx.author.name}, Пауза.")
            except:
                await generate_response(ctx, "error")
        else:
            await generate_response(ctx, "no_perm")

    @commands.command(name="vol")
    async def vol_command(self, ctx, vol: str = None):
        if ctx.author.is_mod:
            try:
                volume = sp.devices()["devices"][0]["volume_percent"]
                if vol is None:
                    await ctx.send(f"@{ctx.author.name}, Громкость: {volume}%")
                elif vol.isnumeric():
                        sp.volume(int(vol))
                        await ctx.send(f"@{ctx.author.name}, Громкость установлена на {vol}%")
                else:
                    await ctx.send(f"@{ctx.author.name}, Используйте !vol число для регулировки.")
            except:
                await generate_response(ctx, "error")
        else:
            await generate_response(ctx, "no_perm")

    @commands.command(name="skip")
    async def skip_song_command(self, ctx):
        if sp.currently_playing():
            try:
                data = sp.currently_playing()
                name = ', '.join([artist["name"] for artist in data["item"]["artists"]])
                song = data['item']['name']
                curr = f"{name} - {song}"

                if curr != self.song_playing:
                    self.song_playing = f"{name} - {song}"
                    self.sk = 0
                    self.las = []
                else:
                    pass

                viewer_count = 0
                headers = {
                    'Client-ID': os.getenv('TW_CLIENT'),
                    'Authorization': f"Bearer {os.getenv('TW_OAUTH')}",
                }

                url = f'https://api.twitch.tv/helix/streams?user_login={self.initial_channels[0]}'
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        data = await resp.json()
                        viewer_count = data['data'][0]['viewer_count']

                if viewer_count <= 2: viewer_count = 1
                elif viewer_count <= 4: viewer_count = 2
                else: viewer_count //= 3
                
                if ctx.author.name.lower() in self.las:
                    if self.sk >= viewer_count:
                        await ctx.send(f"Скипаем... ({self.sk}/{viewer_count})")
                        sp.next_track()
                        self.las = []
                        self.sk = 0
                    else:
                        await ctx.send(f'@{ctx.author.name}, Вы уже проголосовали ({self.sk}/{viewer_count})')

                else:
                    self.sk += 1
                    if self.sk >= viewer_count:
                        await ctx.send(f"Скипаем... ({self.sk}/{viewer_count})")
                        sp.next_track()
                        self.las = []
                        self.sk = 0
                    else:
                        self.las.append(ctx.author.name.lower())
                        await ctx.send(f'@{ctx.author.name}, Вы проголосовали за скип. ({self.sk}/{viewer_count})')
            except:
                await generate_response(ctx, "error")
        else:
            await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")


    async def generate_response(self, ctx, result):
        if (result == "no_perm"):
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")
        elif (result == "error"):
            await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")


    async def chat_sr(self, ctx, song, song_uri):
        if not song_uri:
            try:
                song_uri = sp.search(song, limit=1, type="track", market="BY")["tracks"]["items"][0]["uri"]
            except:
                try:
                    song_uri = sp.search(song, limit=1, type="track", market="US")["tracks"]["items"][0]["uri"]
                except:
                    await ctx.send(f"@{ctx.author.name}, Эта песня не найдена в Spotify.")
                    return

        elif islink(song_uri):
            try:
                data = sp.track(song_uri)
            except:
                await ctx.send(f"@{ctx.author.name}, Ссылка не поддерживается. Используйте Spotify/YouTube")
            song_uri = data["uri"]
            song_uri = song_uri.replace("spotify:track:", "")

        song_id = song_uri.replace("spotify:track:", "")

        data = sp.track(song_id)
        song_name = data["name"]
        song_artists = data["artists"]
        song_artists_names = [artist["name"] for artist in song_artists]
        duration = data["duration_ms"] / 60000

        if song_uri != "not found":
            if duration > 15:
                await ctx.send(f"@{ctx.author.name}, Трек слишком длинный.")
            else:
                try:
                    sp.add_to_queue(song_uri)
                    await ctx.send(
                        f"@{ctx.author.name}, {', '.join(song_artists_names)} - {song_name} добавлено в очередь."
                    )
                except:
                    await ctx.send(f"@{ctx.author.name}, Запросы музыки временно отключены/недоступны")


def scrape_info(url):
    ydl = YoutubeDL(params={'noplaylist': True, })
    info = ydl.extract_info(url, download=False)
    artist, title = get_artist_title(info['title'])
    return f"{artist} - {title}"


def islink(song):
    url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    return re.match(url_regex, song)

if __name__ == '__main__':
    bot = Bot()
    bot.run()
