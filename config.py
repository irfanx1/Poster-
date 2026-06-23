import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Telegram credentials (get API_ID/API_HASH from my.telegram.org) ---
    API_ID = int(os.environ.get("API_ID", "39407537"))
    API_HASH = os.environ.get("API_HASH", "5bd2e83dd1227da3f38c966d1d46d9ae")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8542661280:AAE6uYIUfU2lmqq_DRKGclM1HaStLjeB91M")

    # --- MyAnimeList search via Jikan (unofficial MAL API, no auth needed) ---
    JIKAN_BASE_URL = "https://api.jikan.moe/v4"

    # --- AniList GraphQL endpoint (no auth needed for public search) ---
    ANILIST_API_URL = "https://graphql.anilist.co"

    # --- Search / pagination behaviour ---
    RESULTS_PER_PAGE = 5
    MAX_RESULTS = 20

    # --- Paths ---
    DOWNLOAD_DIR = "downloads"
    TEMPLATE_DIR = "templates"
    FONT_PATH = os.path.join(TEMPLATE_DIR, "fonts", "default.ttf")
    FONT_PATH_BOLD = os.path.join(TEMPLATE_DIR, "fonts", "default_bold.ttf")

    # --- Banner defaults — purely a placeholder template.            ---
    # --- Replace the drawing logic in helpers/banner.py with your    ---
    # --- own design once you have the final template ready.          ---
    BANNER_WIDTH = 1280
    BANNER_HEIGHT = 720
