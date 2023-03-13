##  spotify-twitch-requests

#### Twitch бот на Python для управления очередью воспроизведения Spotify. 

## Требования

* Python
* Аккаунт Twitch для бота
* Аккаунт Spotify с Premium 

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
* `DEV`
