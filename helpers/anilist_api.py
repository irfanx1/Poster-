"""
AniList API wrapper (GraphQL, no auth required for public search/detail
queries). Docs: https://docs.anilist.co
"""

import aiohttp

from config import Config

SEARCH_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME) {
      id
      title { romaji english native }
      format
      seasonYear
      episodes
      coverImage { extraLarge large }
    }
  }
}
"""

DETAIL_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title { romaji english native }
    format
    seasonYear
    episodes
    coverImage { extraLarge large }
    bannerImage
    description(asHtml: false)
  }
}
"""


def _pick_title(t: dict) -> str:
    return t.get("english") or t.get("romaji") or t.get("native") or "Unknown"


async def search_anime(query: str, limit: int = 10) -> list[dict]:
    payload = {"query": SEARCH_QUERY, "variables": {"search": query, "page": 1, "perPage": limit}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.ANILIST_API_URL, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
    except Exception:
        return []

    media = (data.get("data") or {}).get("Page", {}).get("media", []) or []
    results = []
    for m in media:
        cover = m.get("coverImage") or {}
        results.append({
            "source": "anilist",
            "id": m["id"],
            "title": _pick_title(m.get("title") or {}),
            "year": m.get("seasonYear"),
            "format": m.get("format"),
            "episodes": m.get("episodes"),
            "cover": cover.get("extraLarge") or cover.get("large"),
        })
    return results


async def get_anime(anime_id: int) -> dict | None:
    payload = {"query": DETAIL_QUERY, "variables": {"id": anime_id}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.ANILIST_API_URL, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception:
        return None

    m = (data.get("data") or {}).get("Media")
    if not m:
        return None

    cover = m.get("coverImage") or {}
    return {
        "source": "anilist",
        "id": m["id"],
        "title": _pick_title(m.get("title") or {}),
        "year": m.get("seasonYear"),
        "format": m.get("format"),
        "episodes": m.get("episodes"),
        "cover": cover.get("extraLarge") or cover.get("large"),
        "banner": m.get("bannerImage"),
        "description": (m.get("description") or "").replace("<br>", " ")[:400],
    }
