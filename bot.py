import asyncio
import os
import re
import urllib.request
import datetime

from base64 import b64decode
from threading import Thread
from dotenv import load_dotenv
from requests import Session, get
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from twitchio.ext import commands
from youtube_dl import YoutubeDL
from youtube_title_parse import get_artist_title


sk = 0
las = []
load_dotenv()
version = "test"
songts = "AAA - AAA"
targetver = 0

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
            initial_channels=[os.getenv('STREAMER')],
        )

    async def event_ready(self):

        print(f"Бот v{str(version)} ({self.nick}) подключается к чату {os.getenv('STREAMER')}")

    @commands.command(name="up")
    async def upd_command(self, ctx):
        global version
        global targetver
        if ctx.author.name.lower() == os.getenv('DEV').lower():
            await self.isup(ctx)
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")


    @commands.command(name="ping")
    async def ping_command(self, ctx):
        await ctx.send(f"Бот v{str(version)} тут!")


    @commands.command(name="np", aliases=["nowplaying", "song", "current"])
    async def np_command(self, ctx):
        data = sp.currently_playing()
        song_artists = data["item"]["artists"]
        song_artists_names = [artist["name"] for artist in song_artists]
        await ctx.send(
            f"@{ctx.author.name}, Щас играет {', '.join(song_artists_names)} - {data['item']['name']}" # {data['item']['external_urls']['spotify']}"
        )

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
                await self.chat_song_request(ctx, song_uri, song_uri, album=False)
        else:
            await self.chat_song_request(ctx, song, song_uri, album=False)
   

    @commands.command(name="fskip")
    async def fskip_song_command(self, ctx):
        global sk
        global las
        if ctx.author.is_mod:
            las = []
            sk = 0
            await ctx.send(f"pepeDS Скипаем...")
            sp.next_track()
        else:
            await ctx.send(f"@{ctx.author.name}, У тебя нет прав на эту команду!")



    @commands.command(name="skip")
    async def skip_song_command(self, ctx):
        global songts
        global sk
        global las
        data = sp.currently_playing()
        name = ', '.join([artist["name"]
                         for artist in data["item"]["artists"]])
        song = data['item']['name']
        curr = f"{name} - {song}"

        if curr != songts:
            songts = f"{name} - {song}"
            sk = 0
            las = []
        else:
            pass

        vvs = 0
        headers = {
            'Client-ID': os.getenv('TW_CLIENT'),
            'Authorization': f"Bearer {os.getenv('TW_OAUTH')}",            
        }

        url = f'https://api.twitch.tv/helix/streams?user_login={os.getenv("STREAMER")}'
        try:
            vvs = get(url, headers=headers).json()['data'][0]['viewer_count']
        except:
            vvs = 0
        
        switch = {
        0: 1,
        1: 1,
        2: 1,
        3: 2,
        4: 2,
        }
        vvs = switch.get(vvs, vvs//3)

        if ctx.author.name.lower() in las:
            await ctx.send(f'@{ctx.author.name}, Вы уже проголосовали.')
        else:
            sk += 1
            if sk == vvs:
                sp.next_track()
                await ctx.send(f"pepeDS Скипаем...")
                las = []
                sk = 0
            else:
                sk += 1
                las.append(ctx.author.name.lower())
                await ctx.send(f'@{ctx.author.name}, Вы проголосовали за скип. ({sk}/{vvs})')

    def run_updf(self, ctx, link):
        asyncio.run(self.updf(ctx, link))

    async def isup(self, ctx):
        global version
        global targetver
        if version != "test":
            repo = "ch4og/SpotifyTwitch"
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = get(url)
            if response.status_code == 200:
                release_info = response.json()
                targetver = int(release_info['tag_name'])
                asset_url = None
                for asset in release_info["assets"]:
                    if asset["name"] == "process.exe":
                        asset_url = asset["browser_download_url"]
                        break
                if asset_url is None:
                    print(f"Could not find asset")
                    ctx.send("No asset")
                link = get(asset_url)
                if targetver > int(version):
                    thread = Thread(target=self.run_updf, args=(ctx, link, ))
                    print(f"Downloading update...")
                    thread.start()
                else:
                    print("ERROR: Could not get latest release info.")
                    ctx.send("ERROR")
            else:
                await ctx.send(f"Гений ты сначала патч релизни потом проси обнову (v{version})")
                


            


        else:
            print(f"Test version")

    async def updf(self, ctx, link):
        global targetver
        global version
        urllib.request.urlretrieve(link, "new.exe")
        print("Done.")
        if targetver % 10 == 0:
            specified_datetime = datetime.datetime(2023, 1, 24)
            current_datetime = datetime.datetime.now()
            difference = current_datetime - specified_datetime
            hours = difference.days * 24 / 8
            await ctx.send(f"У бота новая юбилейная версия v{targetver}! Ему уже целых {difference.days} дней! Бот находится в разработке уже {int(hours)} часов! Спасибо за использование бота! <3")

        else:
            await ctx.send(f"v{str(version)} -> v{str(targetver)}")
        os._exit(0)

    async def chat_song_request(self, ctx, song, song_uri, album: bool):
        if song_uri is None:
                data = sp.search(song, limit=1, type="track", market="US")
                try:
                    song_uri = data["tracks"]["items"][0]["uri"]
                except:
                    await ctx.send(f"@{ctx.author.name}, Эта песня не найдена в Spotify.")
                    return

                

        elif re.match(URL_REGEX, song_uri):
            try:
                data = sp.track(song_uri)
            except:
                await ctx.send(f"@{ctx.author.name}, Ссылка не поддерживается")
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
                
                    sp.add_to_queue(song_uri)
                    await ctx.send(
                    f"@{ctx.author.name}, ({song_name} - {', '.join(song_artists_names)}) [ {data['external_urls']['spotify']} ] добавлено в очередь."
                )
                    
                        

# def russi(text):
#     detected_lang = detect(text)
#     if detected_lang != 'ru':
#         # Use the GoogleTranslator class to translate the text to Russian
#         return GoogleTranslator(source='auto', target='ru').translate(text)
#     else:
#         return text

# def engli(text):
#     detected_lang = detect(text)
#     if detected_lang != 'en':
#         # Use the GoogleTranslator class to translate the text to English
#         return GoogleTranslator(source='auto', target='en').translate(text)
#     else:
#         return text

def scrape_info(url):
    ydl = YoutubeDL(params={'noplaylist': True, })
    info = ydl.extract_info(url, download=False)
    artist, title = get_artist_title(info['title'])
    return f"{artist} - {title}"


def bot_app():
    bot = Bot()
    bot.run()



def decode(inp):
    return b64decode(inp).decode("utf-8")


if __name__ == '__main__':

    bot_app()
    