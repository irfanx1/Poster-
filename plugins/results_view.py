from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import Config

RESULTS_HEADER = "**Search results for** `{query}`\n\nPick the matching series:"

SOURCE_TAG = {"anilist": "AniList", "mal": "MAL"}


def build_results_keyboard(session):
    per_page = Config.RESULTS_PER_PAGE
    start = session.page * per_page
    end = start + per_page
    page_results = session.results[start:end]

    rows = []
    for idx, r in enumerate(page_results, start=start):
        label = f"[{SOURCE_TAG.get(r['source'], r['source'])}] {r['title']}"
        if r.get("year"):
            label += f" ({r['year']})"
        rows.append([InlineKeyboardButton(label[:64], callback_data=f"sel:{idx}")])

    nav = []
    if session.page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data="page:prev"))
    total_pages = max(1, (len(session.results) - 1) // per_page + 1)
    nav.append(InlineKeyboardButton(f"{session.page + 1}/{total_pages}", callback_data="noop"))
    if end < len(session.results):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data="page:next"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    text = RESULTS_HEADER.format(query=session.query)
    return text, InlineKeyboardMarkup(rows)
