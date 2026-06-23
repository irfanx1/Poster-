import os

from config import Config
from helpers.banner import generate_banner
from helpers.state import sessions, Step


async def generate_and_send(client, chat_id, session, user_id):
    session.step = Step.GENERATING
    output_path = os.path.join(Config.DOWNLOAD_DIR, f"{user_id}_banner.jpg")

    try:
        generate_banner(session.poster_path, session.title, output_path)
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ Failed to generate banner: {e}")
        sessions.reset(user_id)
        return

    await client.send_photo(
        chat_id=chat_id,
        photo=output_path,
        caption=f"🎉 **{session.title}** poster is ready!",
    )
    await client.send_document(
        chat_id=chat_id,
        document=output_path,
        caption="Here's the full-quality file.",
    )
    sessions.reset(user_id)
