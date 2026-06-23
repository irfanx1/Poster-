import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from helpers import anilist_api, mal_api
from helpers.state import sessions, Step
from plugins.results_view import build_results_keyboard


def _merge_results(anilist_results: list, mal_results: list) -> list:
    """Keep AniList + MAL results side by side (not deduped) so the user can
    pick whichever source/edition they prefer."""
    merged = list(anilist_results) + list(mal_results)
    return merged[:Config.MAX_RESULTS]


async def run_search(client: Client, message: Message, query: str):
    if not query:
        await message.reply_text("Usage: `/anime Naruto`")
        return

    session = sessions.get(message.from_user.id)
    session.query = query
    session.page = 0

    status = await message.reply_text(f"🔎 Searching for **{query}**…")

    anilist_results, mal_results = await asyncio.gather(
        anilist_api.search_anime(query, limit=10),
        mal_api.search_anime(query, limit=10),
        return_exceptions=True,
    )
    if isinstance(anilist_results, Exception):
        anilist_results = []
    if isinstance(mal_results, Exception):
        mal_results = []

    merged = _merge_results(anilist_results, mal_results)

    if not merged:
        await status.edit_text("No results found on AniList or MyAnimeList. Try another name.")
        return

    session.results = merged
    session.step = Step.SELECT_RESULT

    text, markup = build_results_keyboard(session)
    await status.edit_text(text, reply_markup=markup, disable_web_page_preview=True)


@Client.on_message(filters.command("anime"))
async def anime_cmd(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    query = parts[1].strip() if len(parts) > 1 else ""
    await run_search(client, message, query)


@Client.on_message(
    filters.text & filters.private & ~filters.command(["start", "help", "cancel", "anime"])
)
async def text_router(client: Client, message: Message):
    """Routes plain text depending on session state:
    - IDLE -> treat the text as an anime search query
    - AWAIT_CUSTOM_TITLE -> capture the custom title
    - anything else -> nudge the user toward the buttons
    """
    session = sessions.get(message.from_user.id)

    if session.step == Step.AWAIT_CUSTOM_TITLE:
        from plugins.title_flow import receive_custom_title
        await receive_custom_title(client, message, session)
        return

    if session.step == Step.IDLE:
        await run_search(client, message, message.text.strip())
        return

    await message.reply_text(
        "Please use the buttons above, or send /cancel to start a new search."
    )
