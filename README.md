# Anime Poster Generator — Telegram Bot

Pyrogram-based bot. Send an anime name, pick the right series from
**AniList + MyAnimeList** results, choose official/custom title and
official/custom poster, and get a generated banner back.

## Structure

```
anime-poster-bot/
├── main.py                 # entrypoint — only runs the bot
├── bot.py                  # Client subclass (Pyrogram app config)
├── config.py                # all settings / env vars / tunables
├── requirements.txt
├── .env.example
├── helpers/
│   ├── state.py              # in-memory per-user session/FSM
│   ├── anilist_api.py        # AniList GraphQL search + detail
│   ├── mal_api.py             # MyAnimeList search + detail (via Jikan)
│   └── banner.py              # 🎨 BANNER DESIGN LOGIC — edit this file
└── plugins/                  # Pyrogram auto-loads everything here
    ├── start.py               # /start /help /cancel
    ├── search.py               # /anime <name> + plain-text search
    ├── results_view.py          # paginated results keyboard
    ├── callback.py               # all inline-button callbacks
    ├── title_flow.py              # official vs custom title step
    ├── poster_flow.py              # official vs custom poster step
    └── generate.py                  # calls helpers/banner.py, sends result
```

## Setup

```bash
cd anime-poster-bot
pip install -r requirements.txt
cp .env.example .env
# fill in API_ID, API_HASH (my.telegram.org) and BOT_TOKEN (@BotFather)
python main.py
```

## How it works

1. User sends `/anime Naruto` or just types `Naruto`.
2. Bot queries **AniList** (GraphQL) and **MyAnimeList** (via the free
   Jikan API) in parallel and shows a combined, paginated, tagged list
   (`[AniList] Naruto`, `[MAL] Naruto Shippuden`, …) as inline buttons.
3. User taps a result → bot fetches full detail and shows the cover +
   asks **Official Title** vs **Custom Title**.
4. If custom, bot waits for the next text message as the title.
5. Bot asks **Official Poster** vs **Custom Poster** (upload your own).
6. Bot generates the banner (`helpers/banner.py`) and sends it back as
   both a photo and a full-quality document.

State is tracked per-user in `helpers/state.py` (in-memory — swap for
Redis/SQLite if you need it to survive restarts).

## 🎨 Adding your banner design

Everything funnels into one function:

```python
# helpers/banner.py
def generate_banner(poster_path: str, title: str, output_path: str) -> str:
    ...
```

It currently does a simple "cover image + gradient + centered title"
placeholder so the bot works immediately. Replace the body with your
real template logic (load a PSD/PNG template, composite logos, custom
fonts, frames, etc.) — no other file needs to change. Put any custom
fonts in `templates/fonts/` and point `Config.FONT_PATH` /
`FONT_PATH_BOLD` at them.

## Notes

- Jikan (MAL) is rate-limited to ~3 req/s / 60 per minute — fine for
  normal bot traffic.
- AniList's public GraphQL endpoint needs no API key.
- Want the official MAL API instead of Jikan? Add `MAL_CLIENT_ID` to
  `config.py` and swap the requests in `helpers/mal_api.py` for calls to
  `https://api.myanimelist.net/v2/anime`.
