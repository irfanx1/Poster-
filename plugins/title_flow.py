from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from helpers.state import sessions, Step


async def handle_title_choice(client, query):
    session = sessions.get(query.from_user.id)
    choice = query.data.split(":")[1]

    if choice == "official":
        session.title = session.selected["title"]
        await ask_poster_choice(client, query.message, session)
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
    await ask_poster_choice(client, message, session)


async def ask_poster_choice(client, message, session):
    session.step = Step.POSTER_CHOICE
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Official Poster", callback_data="poster:official"),
         InlineKeyboardButton("📤 Upload Custom Poster", callback_data="poster:custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])
    await client.send_message(
        chat_id=message.chat.id,
        text="Now, do you want to use the **official poster/cover** or **upload your own image**?",
        reply_markup=markup,
    )
