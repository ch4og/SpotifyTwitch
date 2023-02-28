## `🎶`  spotify-twitch-requests

#### Twitch бот на Python для управления очередью воспроизведения Spotify. 

## `💻` Требования

1. Python
2. Аккаунт Twitch для бота
3. Аккаунт Spotify с Premium 

### `✨` Необходимо

1. [Bot Token](https://twitchapps.com/tmi/)
2. [Twitch Application](https://dev.twitch.tv/console/apps/create)
   - Создать приложение чат-бот
   - OAuth redirect URL должны быть `http://localhost:17563/` и `http://localhost:17563`
3. [Spotify Application](https://developer.spotify.com/dashboard/applications)
   - Установить сайт и Redirect URLs `http://localhost:8080`

### `🫖` Переменные в .env
1. SP_CLIENT
2. SP_SECRET
3. TW_OAUTH
4. TW_CLIENT
5. BOT_NICK
6. PREFIX
7. STREAMER
8. DEV
