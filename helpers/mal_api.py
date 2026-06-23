"""
MyAnimeList data via Jikan (https://jikan.moe) — a free, unofficial REST
wrapper around MAL that needs no API key/OAuth, unlike the official MAL API.

If you'd rather use the official MAL API (needs a Client ID from
https://myanimelist.net/apiconfig), swap the requests below for calls to
https://api.myanimelist.net/v2/anime and add MAL_CLIENT_ID to config.py.

Note: Jikan is rate-limited (~3 req/s, 60/min) — fine for normal bot usage.
"""

import aiohttp

from config import Config


async def search_anime(query: str, limit: int = 10) -> list[dict]:
    url = f"{Config.JIKAN_BASE_URL}/anime"
    params = {"q": query, "limit": limit}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
    except Exception:
        return []

    results = []
    for a in data.get("data", []) or []:
        images = (a.get("images") or {}).get("jpg") or {}
        results.append({
            "source": "mal",
            "id": a["mal_id"],
            "title": a.get("title") or "Unknown",
            "year": a.get("year"),
            "format": a.get("type"),
            "episodes": a.get("episodes"),
            "cover": images.get("large_image_url") or images.get("image_url"),
        })
    return results


async def get_anime(anime_id: int) -> dict | None:
    url = f"{Config.JIKAN_BASE_URL}/anime/{anime_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception:
        return None

    a = data.get("data")
    if not a:
        return None

    images = (a.get("images") or {}).get("jpg") or {}
    trailer = (a.get("trailer") or {}).get("images") or {}
    return {
        "source": "mal",
        "id": a["mal_id"],
        "title": a.get("title") or "Unknown",
        "year": a.get("year"),
        "format": a.get("type"),
        "episodes": a.get("episodes"),
        "cover": images.get("large_image_url") or images.get("image_url"),
        "banner": trailer.get("maximum_image_url"),
        "description": (a.get("synopsis") or "")[:400],
    }
