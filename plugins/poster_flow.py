import os

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from helpers.state import sessions, Step


async def handle_poster_choice(client, query):
    session = sessions.get(query.from_user.id)
    choice = query.data.split(":")[1]

    if choice == "official":
        await query.answer("Downloading official poster…")
        path = await _download_image(session.selected["cover"], query.from_user.id)
        if not path:
            await query.message.edit_text("⚠️ Couldn't download the official poster. Try uploading your own.")
            return
        session.poster_path = path
        await query.message.edit_text("✅ Using official poster. Generating your banner…")
        await _trigger_generation(client, query.message.chat.id, session, query.from_user.id)
        return

    session.step = Step.AWAIT_CUSTOM_POSTER
    await query.message.edit_text(
        "📤 Send me the image you want to use as the poster (as a photo or as a file)."
    )
    await query.answer()


async def _download_image(url: str, user_id: int) -> str | None:
    if not url:
        return None
    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
    dest = os.path.join(Config.DOWNLOAD_DIR, f"{user_id}_source.jpg")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=20) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest
    except Exception:
        return None


async def _trigger_generation(client, chat_id, session, user_id):
    from plugins.generate import generate_and_send
    await generate_and_send(client, chat_id, session, user_id)


@Client.on_message(filters.photo & filters.private)
async def receive_custom_poster_photo(client: Client, message: Message):
    session = sessions.get(message.from_user.id)
    if session.step != Step.AWAIT_CUSTOM_POSTER:
        return

    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
    dest = os.path.join(Config.DOWNLOAD_DIR, f"{message.from_user.id}_source.jpg")
    await message.download(file_name=dest)
    session.poster_path = dest

    await message.reply_text("✅ Custom poster received. Generating your banner…")
    from plugins.generate import generate_and_send
    await generate_and_send(client, message.chat.id, session, message.from_user.id)


@Client.on_message(filters.document & filters.private)
async def receive_custom_poster_doc(client: Client, message: Message):
    session = sessions.get(message.from_user.id)
    if session.step != Step.AWAIT_CUSTOM_POSTER:
        return

    if not (message.document.mime_type or "").startswith("image/"):
        await message.reply_text("Please send an image file.")
        return

    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
    dest = os.path.join(Config.DOWNLOAD_DIR, f"{message.from_user.id}_source.jpg")
    await message.download(file_name=dest)
    session.poster_path = dest

    await message.reply_text("✅ Custom poster received. Generating your banner…")
    from plugins.generate import generate_and_send
    await generate_and_send(client, message.chat.id, session, message.from_user.id)
