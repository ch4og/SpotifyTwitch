##  spotify-twitch-requests

#### Twitch бот на Python для управления очередью воспроизведения Spotify
##### С поддержкой gpt-3.5-turbo
## Требования

* Аккаунт Twitch для бота
* Аккаунт Spotify с Premium 
* OpenAI API для команды `!gpt`

### Необходимо

* [Bot Token](https://twitchapps.com/tmi/)
* [Twitch Application](https://dev.twitch.tv/console/apps/create)
   - Создать приложение чат-бот
   - OAuth redirect URL должны быть `http://localhost:17563/` и `http://localhost:17563`
* [Spotify Application](https://developer.spotify.com/dashboard/applications)
   - Установить сайт и Redirect URLs `http://localhost:8080`

### Переменные в .env
* `SP_CLIENT`
* `SP_SECRET`
* `TW_OAUTH` На самом деле это токен (https://twitchtokengenerator.com/)
* `TW_CLIENT`
* `BOT_NICK`
* `PREFIX`
* `STREAMER`
* `OPENAI`

#### Бот имеет плохую систему обновлений. Запускать через что-то подобное:

```batch
if exist new.exe (
    del process.exe
    move new.exe process.exe
)
process.exe 
``` 
