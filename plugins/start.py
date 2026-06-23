from pyrogram import Client, filters
from pyrogram.types import Message

from helpers.state import sessions

HELP_TEXT = (
    "**🎬 Anime Poster Generator**\n\n"
    "Send me an anime name (or use `/anime <name>`) and I'll pull results "
    "from **AniList** and **MyAnimeList**, then walk you through building "
    "a poster step by step:\n\n"
    "1️⃣ Pick the matching series\n"
    "2️⃣ Choose official or custom title\n"
    "3️⃣ Choose official or custom poster image\n"
    "4️⃣ Get your generated banner\n\n"
    "**Commands**\n"
    "• `/anime <name>` — search for an anime\n"
    "• `/cancel` — cancel the current session\n"
    "• `/help` — show this message"
)


@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    sessions.reset(message.from_user.id)
    await message.reply_text(HELP_TEXT)


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)


@Client.on_message(filters.command("cancel"))
async def cancel_cmd(client: Client, message: Message):
    sessions.reset(message.from_user.id)
    await message.reply_text("❌ Session cancelled. Send an anime name to start again.")
