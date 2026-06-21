import os
import logging

from pyrogram import Client

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

log = logging.getLogger("AnimePosterBot")


class AnimePosterBot(Client):
    """Main bot client. Plugins are auto-loaded from the plugins/ package."""

    def __init__(self):
        super().__init__(
            name="anime_poster_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50,
        )

    async def start(self):
        await super().start()
        os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
        me = await self.get_me()
        self.username = me.username
        log.info(f"Bot started as @{me.username}")

    async def stop(self, *args):
        await super().stop()
        log.info("Bot stopped.")
