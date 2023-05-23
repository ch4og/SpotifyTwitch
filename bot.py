import asyncio
import os
import re
import urllib.request
import openai
import twitchio

from requests import get
from threading import Thread
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from twitchio.ext import commands
from yt_dlp import YoutubeDL
from youtube_title_parse import get_artist_title

# TODO: Написать гайд по развертыванию бота из сурсов. Переписать все try/except с учетом ошибок.

sk = 0
ls = []
load_dotenv()
repo = "ch4og/spotify-twitch-requests"
song_playing = "AAA - AAA"
streamer_name = os.getenv('STREAMER')
openai.api_key = os.getenv('OPENAI')


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
            token=os.getenv('TW_OAUTH'),
            client_id=os.getenv('TW_CLIENT'),
            nick=os.getenv('BOT_NICK'),
            prefix=os.getenv('PREFIX'),
            initial_channels=[streamer_name],
        )

    async def event_ready(self):
        print(f"{self.nick} подключается к чату {streamer_name}")

    @commands.command(name="gpt")
    async def gpt_command(self, ctx, *, prompt: str = None):
        if prompt is not None:
            prompt = f"""Ты - искусственный интеллект под названием @{self.nick}. Тебя разработал @ch4ogg. Используй не более 200 символов в ответе. Запрос начинается с следущего предложения. {prompt}"""
            await ctx.send(f"@{ctx.author.name}, {self.generate_text(ctx, prompt)}")
        else:
            await ctx.send(f"@{ctx.author.name}, Привет. Я - ИИ под именем @{self.nick}. Укажите текст вопроса!")

    @commands.command(name="np", aliases=["song"])
    async def np_command(self, ctx):
        data = sp.currently_playing()
        if ctx.channel.is_live:
            try:
                song_artists = data["item"]["artists"]
                song_artists_names = [artist["name"] for artist in song_artists]
                await ctx.send(
                    f"@{ctx.author.name}, Сейчас играет {', '.join(song_artists_names)} - {data['item']['name']}"
                )
            except:
                await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")
        else:
            await ctx.send(f"@{ctx.author.name}, Сейчас не идет стрим.")

    @commands.command(name="sr", aliases=["p"])
    async def sr_command(self, ctx, *, song: str = None):
        if song is None:
            await ctx.send(f"@{ctx.author.name}, Укажите название/ссылку на песню!")
            return
        song_uri = None
        if (
            song.startswith("spotify:track:") or islink(song) and not song.startswith("spotify:track:")):
            nss = song
            if "youtu" in song:
                try:
                    song = scrape_info(nss)
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
        global sk
        global las
        if ctx.author.is_mod:
            las = []
            sk = 0
            if sp.currently_playing() is not None:
                try:
                    sp.next_track()
                    await ctx.send(f"@{ctx.author.name}, Скипаем...")
                except:
                    await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")
            else:
                await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="pause")
    async def pause_song_command(self, ctx):
        if ctx.author.is_mod:
            try:
                sp.pause_playback()
                await ctx.send(f"@{ctx.author.name}, Пауза.")
            except:
                pass
                await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="resume")
    async def resume_song_command(self, ctx):
        if ctx.author.is_mod:
            try:
                sp.start_playback()
                await ctx.send(f"@{ctx.author.name}, Воспроизведение.")
            except:
                await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="vol")
    async def vol_command(self, ctx, vol: str = None):
        if ctx.author.is_mod:
            try:
                volume = sp.devices()["devices"][0]["volume_percent"]
                if vol is None:
                    await ctx.send(f"@{ctx.author.name}, Громкость: {volume}%")
                elif vol.isnumeric():
                        if (int(vol) > 100): 
                            vol = 100
                        sp.volume(int(vol))
                        await ctx.send(f"@{ctx.author.name}, Громкость установлена на {vol}%")
                else:
                    await ctx.send(f"@{ctx.author.name}, Используйте !vol число для регулировки.")
            except:
                await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="skip")
    async def skip_song_command(self, ctx):
        global song_playing
        global sk
        global las
        global streamer_name
        if sp.currently_playing() is not None:
            try:
                data = sp.currently_playing()
                name = ', '.join([artist["name"] for artist in data["item"]["artists"]])
                song = data['item']['name']
                curr = f"{name} - {song}"

                if curr != song_playing:
                    song_playing = f"{name} - {song}"
                    sk = 0
                    las = []
                else:
                    pass

                vvs = 0
                headers = {
                    'Client-ID': os.getenv('TW_CLIENT'),
                    'Authorization': f"Bearer {os.getenv('TW_OAUTH')}",
                }

                url = f'https://api.twitch.tv/helix/streams?user_login={streamer_name}'
                vvs = get(url, headers=headers).json()['data'][0]['viewer_count']

                switch = {
                    0: 1,
                    1: 1,
                    2: 1,
                    3: 2,
                    4: 2,
                }
                vvs = switch.get(vvs, vvs//3)
                if ctx.author.name.lower() in las:
                    if sk >= vvs:
                        await ctx.send(f"Скипаем... ({sk}/{vvs})")
                        sp.next_track()
                        las = []
                        sk = 0
                    else:
                        await ctx.send(f'@{ctx.author.name}, Вы уже проголосовали ({sk}/{vvs})')

                else:
                    sk += 1
                    if sk >= vvs:
                        await ctx.send(f"Скипаем... ({sk}/{vvs})")
                        sp.next_track()
                        las = []
                        sk = 0
                    else:
                        las.append(ctx.author.name.lower())
                        await ctx.send(f'@{ctx.author.name}, Вы проголосовали за скип. ({sk}/{vvs})')
            except:
                await ctx.send(f"@{ctx.author.name}, Произошла ошибка.")
        else:
            await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")


    def generate_text(self, ctx, prompt):
        input_text = prompt
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": input_text}]
                )
            return response['choices'][0]['message']['content'][0:300]
        except:
            return "Произошла ошибка."

    async def chat_sr(self, ctx, song, song_uri):
        if song_uri is None:
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
        song_artists_names = [artist["name"]
                              for artist in song_artists]
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
