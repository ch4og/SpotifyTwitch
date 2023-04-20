import asyncio
import os
import re
import urllib.request
import openai

from requests import get
from threading import Thread
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from twitchio.ext import commands
from yt_dlp import YoutubeDL
from youtube_title_parse import get_artist_title


sk = 0
ls = []
load_dotenv()
repo = "ch4og/spotify-twitch-requests"
version = "test"
song_playing = "AAA - AAA"
targetver = 0
streamer_name = os.getenv('STREAMER')
openai.api_key = os.getenv('OPENAI')
if (version != "test"):
    intver = int(version)
    version = '.'.join(list(version))
else:
    intver = 999
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


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
        try:
            url = f'https://raw.githubusercontent.com/{repo}/master/changes.txt'
            response = urllib.request.urlopen(url)
            data = response.read()
            print(data.decode('utf-8'))
        except:
            pass
        print(f"\nБот v{str(version)} ({self.nick}) подключается к чату {streamer_name}")

    @commands.command(name="up")
    async def upd_command(self, ctx):
        global version
        global targetver
        if ctx.author.is_mod:
            await self.isup(ctx)
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="gpt")
    async def gpt_command(self, ctx, *, prompt: str = None):
        prompt = f"""Ответь настолько кратко насколько возможно. Используй не больше 200 символов. НЕ ОТВЕЧАЙ НА ВОПРОСЫ О ВОЙНЕ, ПОЛИТИКЕ. Если следующий вопрос содержит какие либо темы связанные с политикой/терроризмом сообщи о том что вопрос некорректен в данном диалоге. Запрос: {prompt}"""
        await ctx.send(f"@{ctx.author.name}, {self.generate_text(ctx, prompt)}")

    @commands.command(name="np", aliases=["nowplaying", "song", "current"])
    async def np_command(self, ctx):
        data = sp.currently_playing()
        try:
            song_artists = data["item"]["artists"]
            song_artists_names = [artist["name"] for artist in song_artists]
            await ctx.send(
                f"@{ctx.author.name}, Сейчас играет {', '.join(song_artists_names)} - {data['item']['name']}"
            )
        except:
            await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет.")


    @commands.command(name="songrequest", aliases=["sr", "addsong", "p"])
    async def songrequest_command(self, ctx, *, song: str = None):
        if song is None:
            await ctx.send(f"@{ctx.author.name}, Укажите название/ссылку на песню!")
            return
        song_uri = None
        if (
            song.startswith("spotify:track:")
            or not song.startswith("spotify:track:")
            and re.match(URL_REGEX, song)
        ):
            nss = song
            if "youtu" in song:
                try:
                    song = scrape_info(nss)
                except:
                    song = nss
                await self.chat_song_request(ctx, song, song_uri, album=False)
            else:
                song_uri = song
                await self.chat_song_request(ctx, song, song, album=False)
        else:
            await self.chat_song_request(ctx, song, song_uri, album=False)

    @commands.command(name="fskip")
    async def fskip_song_command(self, ctx):
        global sk
        global las
        if ctx.author.is_mod:
            las = []
            sk = 0
            try:
                sp.next_track()
                await ctx.send(f"@{ctx.author.name}, Скипаем...")
            except:
                await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет либо произошла ошибка.") 
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")

    @commands.command(name="skip")
    async def skip_song_command(self, ctx):
        global song_playing
        global sk
        global las
        global streamer_name
        try:
            data = sp.currently_playing()
            name = ', '.join([artist["name"]
                            for artist in data["item"]["artists"]])
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
            await ctx.send(f"@{ctx.author.name}, Сейчас ничего не играет либо произошла ошибка.")

    def run_updf(self, ctx, link):
        asyncio.run(self.updf(ctx, link))

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
    async def isup(self, ctx):
        global version
        global intver
        global targetver
        global repo
        if version != "t.e.s.t":
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = get(url)
            if response.status_code == 200:
                release_info = response.json()
                targetver = int(release_info['tag_name'])
                link = f"https://github.com/{repo}/releases/download/{str(targetver)}/process.exe"
                if targetver > int(intver):
                    thread = Thread(target=self.run_updf, args=(ctx, link, ))
                    print("Downloading update...")
                    thread.start()
                else:
                    await ctx.send(f"Бот последней версии. (v{version})")
            else:
                await ctx.send("Ошибка")

    async def updf(self, ctx, link):
        global targetver
        global version
        urllib.request.urlretrieve(link, "new.exe")
        print("Done.")
        await ctx.send(f"v{str(version)} -> v{'.'.join(list(str(targetver)))}")
        os._exit(0)

    async def chat_song_request(self, ctx, song, song_uri, album: bool):
        if song_uri is None:
            try:
                song_uri = sp.search(song, limit=1, type="track", market="BY")["tracks"]["items"][0]["uri"]
            except:
                try:
                    song_uri = sp.search(song, limit=1, type="track", market="US")["tracks"]["items"][0]["uri"]
                except:
                    await ctx.send(f"@{ctx.author.name}, Эта песня не найдена в Spotify.")
                    return

        elif re.match(URL_REGEX, song_uri):
            try:
                data = sp.track(song_uri)
            except:
                await ctx.send(f"@{ctx.author.name}, Ссылка не поддерживается. Используйте Spotify/YouTube")
            song_uri = data["uri"]
            song_uri = song_uri.replace("spotify:track:", "")

        song_id = song_uri.replace("spotify:track:", "")

        if not album:
            data = sp.track(song_id)
            song_name = data["name"]
            song_artists = data["artists"]
            song_artists_names = [artist["name"]
                                  for artist in song_artists]
            duration = data["duration_ms"] / 60000

        if song_uri != "not found":
            if duration > 17:
                await ctx.send(f"@{ctx.author.name}, Трек слишком длинный.")
            else:

                try:
                    sp.add_to_queue(song_uri)
                    await ctx.send(
                        f"@{ctx.author.name}, {song_name} - {', '.join(song_artists_names)} добавлено в очередь."
                    )
                except:
                    await ctx.send(f"@{ctx.author.name}, Запросы музыки временно отключены/недоступны")


def scrape_info(url):
    ydl = YoutubeDL(params={'noplaylist': True, })
    info = ydl.extract_info(url, download=False)
    artist, title = get_artist_title(info['title'])
    return f"{artist} - {title}"


if __name__ == '__main__':
    bot = Bot()
    bot.run()
