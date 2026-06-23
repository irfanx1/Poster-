import asyncio
import importlib
import os

from config import Config
from helpers.state import sessions, Step

# Map template IDs (stored in session.template) to their module paths.
# This is the single source of truth — no other file should hard-code a module name.
TEMPLATE_MODULE_MAP = {
    "gen5": "templates.banner_gen5",
}


def _load_template_module(template_id: str):
    """Import and return the template module for the given ID.

    Raises ValueError for unknown IDs so the caller can surface a clear error
    rather than silently falling back to a default.
    """
    module_path = TEMPLATE_MODULE_MAP.get(template_id)
    if module_path is None:
        raise ValueError(
            f"Unknown template '{template_id}'. "
            f"Valid options: {list(TEMPLATE_MODULE_MAP.keys())}"
        )
    return importlib.import_module(module_path)


async def generate_and_send(client, chat_id, session, user_id):
    session.step = Step.GENERATING
    output_path = os.path.join(Config.DOWNLOAD_DIR, f"{user_id}_banner.jpg")
    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

    # ← THE FIX: use exactly the template the user selected — no fallback
    template_id = session.template
    try:
        mod = _load_template_module(template_id)
    except (ValueError, ImportError) as e:
        await client.send_message(chat_id, f"⚠️ Could not load template '{template_id}': {e}")
        sessions.reset(user_id)
        return

    # Build the minimal data/assets dicts expected by render_banner(data, assets, scale, out_path)
    data = {
        "title": session.title,
        "poster_path": session.poster_path,
    }
    assets = {
        "poster": session.poster_path,
    }

    try:
        await asyncio.to_thread(mod.render_banner, data, assets, 1.0, output_path)
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ Failed to generate banner with template '{template_id}': {e}")
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
