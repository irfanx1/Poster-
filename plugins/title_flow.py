from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from helpers.state import sessions, Step

# Maps callback data IDs to human-readable template names.
# Add a new entry here whenever a new template module is added.
TEMPLATES = {
    "gen5": "🎨 Element Vox (Maroon)",
}


async def handle_title_choice(client, query):
    session = sessions.get(query.from_user.id)
    choice = query.data.split(":")[1]

    if choice == "official":
        session.title = session.selected["title"]
        await ask_template_choice(client, query.message, session)
        await query.answer()
        return

    session.step = Step.AWAIT_CUSTOM_TITLE
    try:
        await query.message.edit_caption(
            caption=f"{query.message.caption}\n\n✏️ Send the **custom title** you want on the poster:"
        )
    except Exception:
        await query.message.edit_text("✏️ Send the **custom title** you want on the poster:")
    await query.answer()


async def receive_custom_title(client, message, session):
    title = message.text.strip()
    if not title:
        await message.reply_text("Title can't be empty, send it again:")
        return

    session.title = title
    await message.reply_text(f"✅ Title set to: **{title}**")
    await ask_template_choice(client, message, session)


async def ask_template_choice(client, message, session):
    """Present the template picker. The selected template_id is stored in
    session.template before moving on to poster choice."""
    session.step = Step.TEMPLATE_CHOICE
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"template:{tid}")]
        for tid, label in TEMPLATES.items()
    ]
    buttons.append([InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="cancel")])
    markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id,
        text=(
            "<b><blockquote>🖼 CHOOSE TEMPLATE</blockquote></b>\n"
            "◇ Pick the banner template you want to use for this poster:"
        ),
        reply_markup=markup,
        parse_mode="html",
    )


async def ask_poster_choice(client, message, session):
    session.step = Step.POSTER_CHOICE
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Usᴇ Oғғɪᴄɪᴀʟ Pᴏsᴛᴇʀ", callback_data="poster:official"),
         InlineKeyboardButton("📤 Uᴘʟᴏᴀᴅ Cᴜsᴛᴏᴍ Pᴏsᴛᴇʀ", callback_data="poster:custom")],
        [InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="cancel")],
    ])
    await client.send_message(
        chat_id=message.chat.id,
        text=(
            "<b><blockquote>⟡ POSTER SOURCE</blockquote></b>\n"
            f"◇ Template: <b>{TEMPLATES.get(session.template, session.template)}</b>\n"
            "◇ Would you like to use the official poster or upload your own?"
        ),
        reply_markup=markup,
        parse_mode="html",
    )
