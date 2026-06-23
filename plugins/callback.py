from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from helpers import anilist_api, mal_api
from helpers.state import sessions, Step
from plugins.results_view import build_results_keyboard


@Client.on_callback_query(filters.regex(r"^noop$"))
async def noop_cb(client: Client, query: CallbackQuery):
    await query.answer()


@Client.on_callback_query(filters.regex(r"^cancel$"))
async def cancel_cb(client: Client, query: CallbackQuery):
    sessions.reset(query.from_user.id)
    try:
        await query.message.edit_text("❌ Cancelled. Send an anime name to start again.")
    except Exception:
        await query.message.edit_caption("❌ Cancelled. Send an anime name to start again.")
    await query.answer()


@Client.on_callback_query(filters.regex(r"^page:(prev|next)$"))
async def page_cb(client: Client, query: CallbackQuery):
    session = sessions.get(query.from_user.id)
    direction = query.data.split(":")[1]
    session.page += 1 if direction == "next" else -1
    session.page = max(0, session.page)

    text, markup = build_results_keyboard(session)
    await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    await query.answer()


@Client.on_callback_query(filters.regex(r"^sel:(\d+)$"))
async def select_result_cb(client: Client, query: CallbackQuery):
    session = sessions.get(query.from_user.id)
    idx = int(query.data.split(":")[1])

    if idx >= len(session.results):
        await query.answer("This search expired, please search again.", show_alert=True)
        return

    picked = session.results[idx]
    await query.answer("Fetching details…")

    if picked["source"] == "anilist":
        detail = await anilist_api.get_anime(picked["id"])
    else:
        detail = await mal_api.get_anime(picked["id"])

    if not detail:
        await query.message.edit_text("Couldn't fetch details for that title. Try another result.")
        return

    session.selected = detail
    session.step = Step.TITLE_CHOICE

    caption = (
        f"**{detail['title']}**\n"
        f"Source: {detail['source'].upper()} • {detail.get('format') or '—'} • "
        f"{detail.get('year') or '—'} • {detail.get('episodes') or '—'} eps\n\n"
        "Do you want to use the **official title** or set a **custom title** "
        "for the poster?"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Official Title", callback_data="title:official"),
         InlineKeyboardButton("✏️ Custom Title", callback_data="title:custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])

    try:
        await query.message.delete()
    except Exception:
        pass

    if detail.get("cover"):
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=detail["cover"],
            caption=caption,
            reply_markup=markup,
        )
    else:
        await client.send_message(
            chat_id=query.message.chat.id,
            text=caption,
            reply_markup=markup,
        )


@Client.on_callback_query(filters.regex(r"^title:(official|custom)$"))
async def title_choice_cb(client: Client, query: CallbackQuery):
    from plugins.title_flow import handle_title_choice
    await handle_title_choice(client, query)


@Client.on_callback_query(filters.regex(r"^template:(.+)$"))
async def template_choice_cb(client: Client, query: CallbackQuery):
    """Store the selected template in the session, then advance to poster choice."""
    from plugins.title_flow import ask_poster_choice, TEMPLATES
    session = sessions.get(query.from_user.id)
    template_id = query.data.split(":", 1)[1]

    if template_id not in TEMPLATES:
        await query.answer("Unknown template — please pick one from the list.", show_alert=True)
        return

    # ← THE FIX: persist the user's template choice in the session
    session.template = template_id
    await query.answer(f"✅ Template set: {TEMPLATES[template_id]}")
    await ask_poster_choice(client, query.message, session)


@Client.on_callback_query(filters.regex(r"^poster:(official|custom)$"))
async def poster_choice_cb(client: Client, query: CallbackQuery):
    from plugins.poster_flow import handle_poster_choice
    await handle_poster_choice(client, query)
