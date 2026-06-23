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


def _build_data_for_template(session) -> tuple:
    """
    banner_gen5.render_banner(data, assets, scale, out_path) expects fields
    in AniList's raw GraphQL shape. session.selected uses a flat dict from
    our own API wrappers. This function bridges the two.
    """
    sel = session.selected  # flat dict from anilist_api / mal_api

    # data dict: matches what banner_gen5 reads via data[key] / data.get(key)
    data = {
        # banner_gen5 line 104: data["title"].get("english") or data["title"].get("romaji")
        "title": {
            "english": session.title,   # user's confirmed title (official or custom)
            "romaji":  session.title,
        },
        # line 105: data.get("description", ...)
        "description": sel.get("description", ""),
        # line 175: data.get("genres", [...])
        "genres": sel.get("genres", []),
        # line 230: data.get("startDate", {}).get("year", "N/A")
        "startDate": {"year": sel.get("year", "N/A")},
        # line 231: data.get("status", "N/A")
        "status": (
            "{} ({} EPS)".format(sel.get("format", ""), sel.get("episodes", "?"))
            if sel.get("format") else "N/A"
        ),
        # line 232: data.get("averageScore", 0)
        "averageScore": sel.get("score", 0),
        # line 233: data.get("popularity", 0)
        "popularity": sel.get("popularity", 0),
        # fallback bg if no assets.bg provided
        "coverImage": {"extraLarge": sel.get("cover", "")},
    }

    # assets dict: poster image path is used as background
    # banner_gen5 line 108: assets['bg'][0] if assets.get('bg') else data['coverImage']['extraLarge']
    assets = {
        "bg":   [session.poster_path] if session.poster_path else [],
        "logo": [],   # no logo in this flow; template falls back gracefully
    }

    return data, assets


async def generate_and_send(client, chat_id, session, user_id):
    session.step = Step.GENERATING
    output_path = os.path.join(Config.DOWNLOAD_DIR, "{}_banner.jpg".format(user_id))
    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

    # Use exactly the template the user selected — no fallback
    template_id = session.template
    try:
        mod = _load_template_module(template_id)
    except (ValueError, ImportError) as e:
        await client.send_message(chat_id, "Could not load template '{}': {}".format(template_id, e))
        sessions.reset(user_id)
        return

    data, assets = _build_data_for_template(session)

    try:
        await asyncio.to_thread(mod.render_banner, data, assets, 1.0, output_path)
    except Exception as e:
        await client.send_message(chat_id, "Failed to generate banner with template '{}': {}".format(template_id, e))
        sessions.reset(user_id)
        return

    await client.send_photo(
        chat_id=chat_id,
        photo=output_path,
        caption="**{}** poster is ready!".format(session.title),
    )
    await client.send_document(
        chat_id=chat_id,
        document=output_path,
        caption="Here's the full-quality file.",
    )
    sessions.reset(user_id)
