import os
import time
import html
import asyncio
import requests
import re
import math
import importlib
import glob
import urllib.parse
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageChops
from pyrogram import Client, filters, enums
from pyrogram.types import Message, LinkPreviewOptions, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from core.dynamic import dconfig
from utils.helper import download_thumbnail
from plugins.admin import is_admin as admin

try:
    import config
    DOWNLOAD_DIR = getattr(config, "DOWNLOAD_DIR", "./posters")
    TMDB_API_KEY = getattr(config, "TMDB_API_KEY", None)
    FANART_API_KEY = getattr(config, "FANART_API_KEY", None)
except ImportError:
    DOWNLOAD_DIR = "./posters"
    TMDB_API_KEY = None
    FANART_API_KEY = None

# ==============================================================================
#                               CONSTANTS & APIS
# ==============================================================================
ANILIST_URL = "https://graphql.anilist.co"
MAL_URL     = "https://api.jikan.moe/v4"
KITSU_URL   = "https://kitsu.io/api/edge"

RED        = (229, 9, 20, 255)
WHITE      = (255, 255, 255, 255)
WHITE_DIM  = (210, 210, 215, 255)
GRAY       = (170, 170, 175, 220)
GRAY_DIM   = (140, 140, 145, 180)
BLUE_TITLE = (80, 160, 255, 255)
GOLD       = (255, 200, 40, 255)
TRANS      = (0, 0, 0, 0)

BANNER_CACHE = {}  # The heart of the Live Preview Editor

def cleanup_cache(user_id):
    if user_id in BANNER_CACHE:
        del BANNER_CACHE[user_id]

async def session_timer(user_id, client, chat_id):
    """Background task to abort the session if inactive for 5 minutes."""
    while True:
        await asyncio.sleep(60)
        cache = BANNER_CACHE.get(user_id)
        if not cache:
            break
        # Check if 5 minutes (300 seconds) have passed since last activity
        if time.time() - cache.get('last_active', 0) >= 300:
            msg_id = cache.get('preview_msg_id')
            del BANNER_CACHE[user_id]
            if msg_id:
                try:
                    await client.edit_message_caption(
                        chat_id=chat_id, 
                        message_id=msg_id, 
                        caption="❌ <b>Session aborted due to 5 minutes of inactivity.</b>", 
                        parse_mode=enums.ParseMode.HTML, 
                        reply_markup=None
                    )
                except Exception:
                    pass
            break

def verify_session(query):
    """Verifies user ownership and strictly locks to the specific preview message."""
    user_id = query.from_user.id
    if user_id not in BANNER_CACHE:
        return None # Expired
    cache = BANNER_CACHE[user_id]
    if cache.get('preview_msg_id') and cache['preview_msg_id'] != query.message.id:
        return False # Not your session / Wrong message
    cache['last_active'] = time.time() # Reset inactivity timer
    return cache

# ==============================================================================
#                      KURIGRAM COLORED BUTTON ENGINE
# ==============================================================================
try:
    from pyrogram.enums import ButtonStyle
    HAS_BUTTON_STYLE = True
except ImportError:
    HAS_BUTTON_STYLE = False

def cbtn(text, callback_data=None, url=None, user_id=None, color=None):
    kwargs = {"text": text}
    if callback_data: kwargs["callback_data"] = callback_data
    if url: kwargs["url"] = url
    if user_id: kwargs["user_id"] = user_id
    if HAS_BUTTON_STYLE and color and color != "none":
        style_map = {"blue": ButtonStyle.PRIMARY, "green": ButtonStyle.SUCCESS, "red": ButtonStyle.DANGER}
        if color in style_map: kwargs["style"] = style_map[color]
    return InlineKeyboardButton(**kwargs)

def is_cancel(text):
    return text and str(text).strip().lower() in ['/cancel', 'cancel']

# ==============================================================================
#                              IMAGE UTILS & FONTS 
# ==============================================================================
def font(size: int, weight: str = "bold"):
    _LOCAL = "./banner_fonts/"
    _G, _L, _F = "/usr/share/fonts/truetype/google-fonts/", "/usr/share/fonts/truetype/liberation/", "/usr/share/fonts/truetype/freefont/"
    paths = {
        "bold":   [_LOCAL+"Poppins-Bold.ttf", _G+"Poppins-Bold.ttf", _L+"LiberationSans-Bold.ttf", _F+"FreeSansBold.ttf"],
        "medium": [_LOCAL+"Poppins-Medium.ttf", _G+"Poppins-Medium.ttf", _G+"Poppins-Bold.ttf", _L+"LiberationSans-Bold.ttf"],
        "reg":    [_LOCAL+"Poppins-Regular.ttf", _G+"Poppins-Regular.ttf", _L+"LiberationSans-Regular.ttf", _F+"FreeSans.ttf"],
    }
    for p in paths.get(weight, paths["bold"]):
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def fetch_img(url: str):
    if not url: return None
    try:
        if url.startswith("http://") or url.startswith("https://"):
            r = requests.get(url, timeout=15, headers={"User-Agent": "ElevoxBot/3.0"})
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
        elif os.path.isfile(url): return Image.open(url).convert("RGBA")
    except Exception: return None
    return None

def paste(base: Image.Image, layer: Image.Image, xy: tuple, size: tuple = None) -> None:
    if size: layer = layer.resize(size, Image.LANCZOS)
    x, y = int(xy[0]), int(xy[1])
    ox, oy = max(0, -x), max(0, -y)
    x, y = max(0, x), max(0, y)
    crop = layer.crop((ox, oy, layer.width, layer.height))
    cw, ch = min(crop.width, base.width - x), min(crop.height, base.height - y)
    if cw <= 0 or ch <= 0: return
    crop = crop.crop((0, 0, cw, ch))
    tmp = Image.new("RGBA", base.size, TRANS)
    tmp.paste(crop, (x, y))
    base.alpha_composite(tmp)

def wrap_text(text: str, fnt, max_px: int) -> list:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if fnt.getlength(test) <= max_px: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def shadow_text(draw, xy, text, fnt, fill, shadow=(0, 0, 0, 190), offset=3):
    draw.text((xy[0]+offset, xy[1]+offset), text, font=fnt, fill=shadow)
    draw.text(xy, text, font=fnt, fill=fill)

def fmt_num(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.0f}k"
    return str(n)

def ensure_fallback():
    path = "fallback.jpg"
    if not os.path.exists(path):
        img = Image.new("RGB", (800, 450), (30, 30, 35))
        d = ImageDraw.Draw(img)
        f = font(40, "bold")
        d.text((400 - int(f.getlength("NO IMAGE FOUND"))//2, 180), "NO IMAGE FOUND\nSend Custom Image", font=f, fill=(150, 150, 150), align="center")
        img.save(path)
    return path

def left_gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), TRANS)
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / w
        a = 245 if t < 0.35 else int(245 * (1 - (t - 0.35) / 0.35)) if t < 0.70 else 0
        d.line([(x, 0), (x, h)], fill=(12, 12, 15, a))
    return img

def top_gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), TRANS)
    d = ImageDraw.Draw(img)
    for y in range(h):
        a = int(220 * (1 - y / h) ** 1.2)
        d.line([(0, y), (w, y)], fill=(5, 5, 14, a))
    return img

def bottom_gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), TRANS)
    d = ImageDraw.Draw(img)
    for y in range(h):
        a = int(180 * (y / h) ** 1.4)
        d.line([(0, y), (w, y)], fill=(5, 5, 12, a))
    return img

def icon_calendar(d: ImageDraw.Draw, x, y, s=16):
    lw = max(1, int(s / 16))
    d.rectangle([x, y+int(s*0.2), x+s, y+s], outline=WHITE, width=lw)
    d.line([x, y+int(s*0.4), x+s, y+int(s*0.4)], fill=WHITE, width=lw)
    d.rectangle([x+int(s*0.2), y, x+int(s*0.3), y+int(s*0.2)], fill=WHITE)
    d.rectangle([x+int(s*0.7), y, x+int(s*0.8), y+int(s*0.2)], fill=WHITE)

def icon_person(d: ImageDraw.Draw, x, y, s=16):
    lw = max(1, int(s / 16))
    cx = x + s // 2
    r  = s // 4
    d.ellipse([cx-r, y+int(s*0.1), cx+r, y+int(s*0.1)+r*2], outline=WHITE, width=lw)
    d.arc([x+1, y+s//2+int(s*0.2), x+s-1, y+s+int(s*0.1)], start=180, end=360, fill=WHITE, width=lw)

def icon_book(d: ImageDraw.Draw, x, y, s=16):
    lw = max(1, int(s / 16))
    mid = x + s // 2
    d.line([mid, y+2, mid, y+s-2], fill=WHITE, width=lw)
    d.rectangle([x+1, y+2, x+s-1, y+s-2], outline=WHITE, width=lw)

def icon_play(d: ImageDraw.Draw, x, y, s=16, fill=WHITE):
    d.polygon([(x, y), (x, y + s), (x + s, y + (s // 2))], fill=fill)

def icon_star(d: ImageDraw.Draw, x, y, s=16, fill=GOLD):
    cx, cy, outer_rad, inner_rad = x + s / 2, y + s / 2, s / 2, s / 4
    pts = [(cx + math.cos(math.pi/2 - i*math.pi/5) * (outer_rad if i%2==0 else inner_rad), cy - math.sin(math.pi/2 - i*math.pi/5) * (outer_rad if i%2==0 else inner_rad)) for i in range(10)]
    d.polygon(pts, fill=fill)

def draw_button(canvas, draw, x, y, w, h, text, fnt, bg, fg, border=False, border_col=WHITE, radius=5, play_icon=False):
    btn = Image.new("RGBA", (w, h), TRANS)
    bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle([0, 0, w-1, h-1], radius=radius, fill=bg)
    if border: bd.rounded_rectangle([0, 0, w-1, h-1], radius=radius, outline=border_col, width=1)
    paste(canvas, btn, (x, y))
    tw = int(fnt.getlength(text))
    if play_icon:
        icon_sz = fnt.size - 2
        tot_w = icon_sz + 10 + tw
        sx = x + (w - tot_w) // 2
        iy = y + (h - icon_sz) // 2
        icon_play(draw, sx, iy, icon_sz, fill=fg)
        draw.text((sx + icon_sz + 10, y + (h - fnt.size) // 2 - 1), text, font=fnt, fill=fg)
    else:
        draw.text((x + (w - tw) // 2, y + (h - fnt.size) // 2 - 1), text, font=fnt, fill=fg)

# ==============================================================================
#                           ASSET FETCHING (TMDB + FANART.TV + AL/MAL)
# ==============================================================================
async def fetch_tmdb_images(title: str):
    if not TMDB_API_KEY: return None
    try:
        search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={urllib.parse.quote(title)}"
        res = await asyncio.to_thread(requests.get, search_url, timeout=10)
        results = res.json().get('results', [])
        media_type = 'tv'
        if not results:
            m_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={urllib.parse.quote(title)}"
            m_res = await asyncio.to_thread(requests.get, m_url, timeout=10)
            results = m_res.json().get('results', [])
            if not results: return None
            media_type = 'movie'
            
        tmdb_id = results[0]['id']
        img_url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/images?api_key={TMDB_API_KEY}"
        img_res = await asyncio.to_thread(requests.get, img_url, timeout=10)
        data = img_res.json()
        data['tmdb_id'] = tmdb_id
        data['media_type'] = media_type
        
        if media_type == 'tv':
            ext_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids?api_key={TMDB_API_KEY}"
            try:
                ext_res = await asyncio.to_thread(requests.get, ext_url, timeout=5)
                if ext_res.status_code == 200:
                    data['tvdb_id'] = ext_res.json().get('tvdb_id')
            except Exception: pass
            
        return data
    except Exception: return None

async def fetch_fanart_images(tmdb_id: int, media_type: str, tvdb_id: int = None):
    if not FANART_API_KEY: return None
    try:
        if media_type == 'movie':
            url = f"https://webservice.fanart.tv/v3/movies/{tmdb_id}?api_key={FANART_API_KEY}"
        else:
            if not tvdb_id: return None
            url = f"https://webservice.fanart.tv/v3/tv/{tvdb_id}?api_key={FANART_API_KEY}"
            
        res = await asyncio.to_thread(requests.get, url, timeout=10)
        if res.status_code == 200: return res.json()
        return None
    except: return None

async def search_anime(query: str):
    try:
        q = '''query ($search: String) { Page(page: 1, perPage: 5) { media(search: $search, type: ANIME) { id title { romaji english } startDate { year } } } }'''
        res = await asyncio.to_thread(requests.post, ANILIST_URL, json={'query': q, 'variables': {'search': query}}, timeout=10)
        return res.json().get('data', {}).get('Page', {}).get('media', [])
    except: return []

async def search_mal_anime(query: str):
    try:
        res = await asyncio.to_thread(requests.get, f"{MAL_URL}/anime?q={urllib.parse.quote(query)}&limit=5", timeout=10)
        data = res.json().get('data', [])
        filtered = []
        for r in data:
            title = r.get('title_english') or r.get('title')
            year = r.get('year', 'N/A')
            filtered.append({'id': r['mal_id'], 'title': title, 'year': year})
        return filtered
    except: return []

async def search_tmdb_movies_tv(query: str):
    if not TMDB_API_KEY: return []
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={urllib.parse.quote(query)}"
        res = await asyncio.to_thread(requests.get, url, timeout=10)
        results = res.json().get('results', [])
        filtered = []
        for r in results:
            if r.get('media_type') in ['movie', 'tv']:
                title = r.get('title') or r.get('name')
                year = r.get('release_date') or r.get('first_air_date')
                year = year[:4] if year else 'N/A'
                filtered.append({'id': r['id'], 'title': title, 'year': year})
        return filtered[:5]
    except: return []

async def fetch_anime_data(aid: int):
    try:
        q = '''query ($id: Int) { Media(id: $id, type: ANIME) { id idMal title { romaji english } description(asHtml: false) startDate { year } genres averageScore popularity bannerImage coverImage { extraLarge } characters(role: MAIN, sort: ROLE) { edges { node { image { large } } } } staff(perPage: 10) { edges { role node { name { full } } } } studios(isMain: true) { nodes { name } } } }'''
        res = await asyncio.to_thread(requests.post, ANILIST_URL, json={'query': q, 'variables': {'id': aid}}, timeout=10)
        return res.json().get('data', {}).get('Media')
    except: return None

async def fetch_bg_gallery(data: dict):
    images = [] 
    if data.get('bannerImage'): images.append((data['bannerImage'], "AniList"))
    mal_id = data.get('idMal')
    if mal_id:
        try:
            pic_res = await asyncio.to_thread(requests.get, f"https://api.jikan.moe/v4/anime/{mal_id}/pictures", timeout=10)
            if pic_res.status_code == 200:
                for pic in pic_res.json().get('data', []):
                    img = pic.get('jpg', {}).get('large_image_url') or pic.get('jpg', {}).get('image_url')
                    if img and not any(img in i[0] for i in images): images.append((img, "MAL"))
        except: pass
    if data.get('coverImage', {}).get('extraLarge') and not images: images.append((data['coverImage']['extraLarge'], "AniList"))
    if not images: images.append((ensure_fallback(), "System"))
    return images

async def fetch_char_gallery(data: dict):
    images = [] 
    for edge in data.get('characters', {}).get('edges', []):
        img = edge.get('node', {}).get('image', {}).get('large')
        if img: images.append((img, "AniList"))
    if not images: images.append((ensure_fallback(), "System"))
    return images

async def fetch_logo_gallery(title: str):
    images = [] 
    try:
        url = f"{KITSU_URL}/anime?filter[text]={urllib.parse.quote(title)}"
        r = await asyncio.to_thread(requests.get, url, headers={"Accept": "application/vnd.api+json"}, timeout=10)
        for anime in r.json().get("data", []):
            logo = anime.get("attributes", {}).get("logo")
            if logo and logo.get("original"): images.append((logo.get("original"), "Kitsu"))
    except: pass
    if not images: images.append((ensure_fallback(), "System"))
    return images

# ==============================================================================
#                           DYNAMIC FORMAT LOADER & GRID
# ==============================================================================
async def get_available_formats():
    formats = []
    plugin_dir = os.path.dirname(__file__)
    for file in glob.glob(os.path.join(plugin_dir, "banner_format*.py")):
        mod_name = os.path.basename(file)[:-3]
        try:
            mod = importlib.import_module(f"plugins.Element_Banner.{mod_name}")
            formats.append({
                "id": mod_name,
                "name": getattr(mod, "FORMAT_NAME", mod_name),
                "preview": getattr(mod, "PREVIEW_URL", ensure_fallback()),
                "module": mod
            })
        except Exception as e: print(f"Failed to load {mod_name}: {e}")
    return sorted(formats, key=lambda x: x["id"])

def build_formats_grid(formats, active_id=None, callback_prefix="bfmt_set_"):
    kb = []
    row = []
    for f in formats:
        name = f["name"]
        if active_id and f["id"] == active_id:
            name = f"✅ {name}"
        row.append(cbtn(name, f"{callback_prefix}{f['id']}", color="blue"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    return kb

@Client.on_message(filters.command("banner_format") & admin)
async def list_banner_formats(client, message):
    formats = await get_available_formats()
    if not formats: return await message.reply("❌ No banner formats found in the system!")
    
    active_id = await dconfig.get("ACTIVE_BANNER_FORMAT") or "banner_format1"
    
    preview_url = next((f["preview"] for f in formats if f["id"] == active_id), None)
    if not preview_url or not preview_url.startswith("http"):
        preview_url = ensure_fallback()
        
    kb = build_formats_grid(formats, active_id=active_id, callback_prefix="bfmt_set_")
    kb.append([cbtn("❌ Close", "close_menu", color="red")])
    
    text = (
        "<blockquote expandable><b>🎨 Bᴀɴɴᴇʀ Fᴏʀᴍᴀᴛ Mᴀɴᴀɢᴇʀ</b></blockquote>\n\n"
        "Select a layout below to set it as the <b>Default Format</b> for new generations:"
    )
    
    await client.send_photo(
        message.chat.id, 
        photo=preview_url,
        caption=text, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_callback_query(filters.regex(r"^bfmt_set_(.+)$") & admin)
async def bfmt_set_cb(client, query):
    new_id = query.matches[0].group(1)
    await dconfig.set("ACTIVE_BANNER_FORMAT", new_id)
    await query.answer(f"✅ Default format set to {new_id}!", show_alert=True)
    
    formats = await get_available_formats()
    preview_url = next((f["preview"] for f in formats if f["id"] == new_id), None)
    if not preview_url or not preview_url.startswith("http"):
        preview_url = ensure_fallback()
        
    kb = build_formats_grid(formats, active_id=new_id, callback_prefix="bfmt_set_")
    kb.append([cbtn("❌ Close", "close_menu", color="red")])
    
    text = (
        "<blockquote expandable><b>🎨 Bᴀɴɴᴇʀ Fᴏʀᴍᴀᴛ Mᴀɴᴀɢᴇʀ</b></blockquote>\n\n"
        "Select a layout below to set it as the <b>Default Format</b> for new generations:"
    )
    
    try:
        await query.message.edit_media(
            media=InputMediaPhoto(preview_url, caption=text, parse_mode=enums.ParseMode.HTML),
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception:
        pass

# ==============================================================================
#                               BOT COMMANDS
# ==============================================================================
@Client.on_message(filters.command("banner") & admin)
async def start_banner_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    cleanup_cache(user_id)
    
    query = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else None
    if not query:
        return await message.reply("⚠️ <b>Usage:</b> <code>/banner [Name or ID]</code>\n <blockquote><b>Use: /banner_format to set a default banner format</b></blockquote>", parse_mode=enums.ParseMode.HTML)

    if query.isdigit():
        msg = await message.reply("⏳ <code>Searching...</code>", parse_mode=enums.ParseMode.HTML)
        data = await fetch_anime_data(int(query))
        if not data: return await msg.edit_text("❌ Anime ID not found.")
        await process_banner_setup(client, message.chat.id, message.from_user.id, msg, data)
    else:
        kb = [
            [cbtn("AniList", "bann_eng_ani", color="blue"),
             cbtn("MAL", "bann_eng_mal", color="blue"),
             cbtn("TMDB", "bann_eng_tmdb", color="blue")],
            [cbtn("❌ Cancel", f"bann_cancel_{user_id}", color="red")]
        ]
        BANNER_CACHE[user_id] = {
            'pending_query': query,
            'chat_id': message.chat.id,
            'last_active': time.time()
        }
        await message.reply("🔍 <b>Select Search Engine:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^bann_eng_(ani|mal|tmdb)$") & admin)
async def bann_eng_callback(client: Client, query):
    user_id = query.from_user.id
    cache = BANNER_CACHE.get(user_id)
    if not cache or 'pending_query' not in cache:
        return await query.answer("Session expired.", show_alert=True)
    
    engine = query.matches[0].group(1)
    search_q = cache['pending_query']
    await query.message.edit_text("⏳ <code>Searching...</code>", parse_mode=enums.ParseMode.HTML)
    
    results = []
    if engine == "ani":
        res = await search_anime(search_q)
        for r in res:
            t = r['title'].get('english') or r['title'].get('romaji')
            y = r.get('startDate',{}).get('year', 'N/A')
            results.append({'id': r['id'], 'title': t, 'year': y})
    elif engine == "mal":
        res = await search_mal_anime(search_q)
        for r in res:
            results.append({'id': r['id'], 'title': r['title'], 'year': r['year']})
    elif engine == "tmdb":
        res = await search_tmdb_movies_tv(search_q)
        for r in res:
            results.append({'id': r['id'], 'title': r['title'], 'year': r['year']})
            
    if not results:
        return await query.message.edit_text("❌ No results found.")
        
    cache['search_results'] = results 
    
    kb = []
    for r in results:
        title = str(r['title'])[:40]
        kb.append([cbtn(f"🎬 {title} ({r.get('year', 'N/A')})", f"bann_sel_{engine}_{r['id']}_{user_id}", color="blue")])
    kb.append([cbtn("❌ Cancel", f"bann_cancel_{user_id}", color="red")])
    
    await query.message.edit_text("<blockquote expandable><b>🔍 Bᴀɴɴᴇʀ Sᴇᴀʀᴄʜ Rᴇꜱᴜʟᴛꜱ</b></blockquote>\nSelect the media:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^bann_sel_(ani|mal|tmdb)_(\d+)_(\d+)$") & admin)
async def bann_sel_callback(client: Client, query):
    engine = query.matches[0].group(1)
    media_id = int(query.matches[0].group(2))
    owner_id = int(query.matches[0].group(3))
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your session!", show_alert=True)
        
    await query.message.edit_text("⏳ <code>Fetching assets and preparing Live Editor...</code>", parse_mode=enums.ParseMode.HTML)
    
    cache = BANNER_CACHE.get(owner_id, {})
    results = cache.get('search_results', [])
    selected = next((r for r in results if r['id'] == media_id), None)
    
    data = None
    if engine == "ani":
        data = await fetch_anime_data(media_id)
    elif engine == "mal":
        try:
            res = await asyncio.to_thread(requests.get, f"{MAL_URL}/anime/{media_id}", timeout=10)
            mal_data = res.json().get('data', {})
            data = {
                'id': media_id,
                'idMal': media_id,
                'title': {'english': mal_data.get('title_english') or mal_data.get('title'), 'romaji': mal_data.get('title')},
                'coverImage': {'extraLarge': mal_data.get('images', {}).get('jpg', {}).get('large_image_url')}
            }
        except: pass
    elif engine == "tmdb":
        if selected:
            data = {
                'id': media_id,
                'title': {'english': selected['title']},
                'coverImage': {}
            }
            
    if not data: return await query.message.edit_text("❌ Failed to fetch data.")
    await process_banner_setup(client, query.message.chat.id, owner_id, query.message, data)

@Client.on_callback_query(filters.regex(r"^bann_cancel_(\d+)$") & admin)
async def bann_cancel_callback(client: Client, query):
    owner_id = int(query.matches[0].group(1))
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your session!", show_alert=True)
    await query.message.delete()

# ==============================================================================
#                           THE LIVE EDITOR ENGINE
# ==============================================================================
async def process_banner_setup(client, chat_id, user_id, msg, data):
    title = data['title'].get('english') or data['title'].get('romaji')
    a_id = data.get('id', 'temp')

    tmdb_data = await fetch_tmdb_images(title)
    fanart_data = None
    if tmdb_data and tmdb_data.get('tmdb_id'):
        fanart_data = await fetch_fanart_images(tmdb_data['tmdb_id'], tmdb_data['media_type'], tmdb_data.get('tvdb_id'))
        
    al_mal_bgs = await fetch_bg_gallery(data)
    al_chars = await fetch_char_gallery(data)
    kitsu_logos = await fetch_logo_gallery(title)
    
    assets = {'bgs': [], 'chars': [], 'logos': [], 'posters': []}
    
    # 1. Backgrounds
    if fanart_data:
        for k in ['showbackground', 'moviebackground']:
            assets['bgs'].extend([{'url': i['url'], 'src': 'FanArt'} for i in fanart_data.get(k, [])])
    if tmdb_data and tmdb_data.get('backdrops'):
        textless = [b for b in tmdb_data['backdrops'] if not b.get('iso_639_1')]
        for b in (textless or tmdb_data['backdrops']):
            assets['bgs'].append({'url': f"https://image.tmdb.org/t/p/original{b['file_path']}", 'src': 'TMDB'})
    for url, src in al_mal_bgs: assets['bgs'].append({'url': url, 'src': src})
    
    # 2. Characters (Transparent Art)
    if fanart_data:
        for k in ['characterart', 'movieart', 'hdclearart', 'clearart', 'hdmovieclearart']:
            assets['chars'].extend([{'url': i['url'], 'src': 'FanArt'} for i in fanart_data.get(k, [])])
    for url, src in al_chars: assets['chars'].append({'url': url, 'src': src})
    
    # 3. Logos
    if fanart_data:
        for k in ['clearlogo', 'hdtvlogo', 'hdmovielogo']:
            assets['logos'].extend([{'url': i['url'], 'src': 'FanArt'} for i in fanart_data.get(k, [])])
    if tmdb_data and tmdb_data.get('logos'):
        en_logos = [l for l in tmdb_data['logos'] if l.get('iso_639_1') == 'en']
        for l in (en_logos or tmdb_data['logos']):
            assets['logos'].append({'url': f"https://image.tmdb.org/t/p/original{l['file_path']}", 'src': 'TMDB'})
    for url, src in kitsu_logos: assets['logos'].append({'url': url, 'src': src})
    
    # 4. Posters (Vertical Cover)
    if fanart_data:
        for k in ['tvposter', 'movieposter', 'seasonposter']:
            assets['posters'].extend([{'url': i['url'], 'src': 'FanArt'} for i in fanart_data.get(k, [])])
    if tmdb_data and tmdb_data.get('posters'):
        en_pos = [p for p in tmdb_data['posters'] if p.get('iso_639_1') == 'en']
        other_pos = [p for p in tmdb_data['posters'] if p not in en_pos]
        for p in (en_pos + other_pos):
            assets['posters'].append({'url': f"https://image.tmdb.org/t/p/original{p['file_path']}", 'src': 'TMDB'})
    assets['posters'].append({'url': data.get('coverImage', {}).get('extraLarge', ensure_fallback()), 'src': 'AniList'})
    
    # Remove duplicates
    for k in assets:
        seen = set()
        new_list = []
        for item in assets[k]:
            if item['url'] not in seen:
                seen.add(item['url'])
                new_list.append(item)
        assets[k] = new_list

    active_format = await dconfig.get("ACTIVE_BANNER_FORMAT") or "banner_format1"
    fmt = active_format.replace("banner_", "")
    
    BANNER_CACHE[user_id] = {
        'data': data,
        'assets': assets,
        'idx': {'bg': 0, 'char': 0, 'logo': 0, 'poster': 0},
        'show_logo': True,
        'src_filter': 'ALL',
        'format': fmt,
        'title': title,
        'a_id': a_id,
        'scale': 1.0,
        'custom': {},
        'last_active': time.time(),
        'chat_id': chat_id
    }
    
    asyncio.create_task(session_timer(user_id, client, chat_id))
    await render_banner_preview(client, chat_id, user_id, msg_id_to_edit=msg.id)

async def render_banner_preview(client, chat_id, user_id, msg_id_to_edit=None, status_msg=None):
    cache = BANNER_CACHE.get(user_id)
    if not cache: return
    
    src_filter = cache['src_filter']
    def get_filtered(atype):
        l = cache['assets'].get(f"{atype}s", [])
        return [x for x in l if x['src'] == src_filter] if src_filter != 'ALL' else l
        
    bgs = get_filtered('bg')
    chars = get_filtered('char')
    logos = get_filtered('logo')
    posters = get_filtered('poster')
    
    idx = cache['idx']
    c_bg = cache['custom'].get('bg')
    bg_url = c_bg if c_bg else (bgs[idx['bg'] % len(bgs)]['url'] if bgs else None)
    
    c_char = cache['custom'].get('char')
    char_url = c_char if c_char else (chars[idx['char'] % len(chars)]['url'] if chars else None)
    
    c_logo = cache['custom'].get('logo')
    logo_url = c_logo if c_logo else (logos[idx['logo'] % len(logos)]['url'] if logos and cache['show_logo'] else None)
    
    c_poster = cache['custom'].get('poster')
    poster_url = c_poster if c_poster else (posters[idx['poster'] % len(posters)]['url'] if posters else cache['data'].get('coverImage', {}).get('extraLarge'))
    
    fmt = cache['format']
    if fmt == "format2":
        char_url = poster_url
        
    format_mod = f"banner_{fmt}"
    try:
        mod = importlib.import_module(f"plugins.Element_Banner.{format_mod}")
    except ImportError:
        return 
        
    assets_for_render = {
        'bg': [bg_url, "API"] if bg_url else None,
        'char': [char_url, "API"] if char_url else None,
        'logo': [logo_url, "API"] if logo_url else None
    }
    
    patched_data = cache['data'].copy()
    if 'coverImage' not in patched_data: patched_data['coverImage'] = {}
    patched_data['coverImage']['extraLarge'] = poster_url
    
    out_path = os.path.join(DOWNLOAD_DIR, f"preview_{user_id}_{int(time.time())}.png")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Fast rendering for Live Preview
    await asyncio.to_thread(mod.render_banner, patched_data, assets_for_render, 0.7, out_path)
    
    # ---------------- BUILD KEYBOARD ----------------
    buttons = []
    
    # Image Cycler
    if len(bgs) > 1 or c_bg:
        buttons.append([cbtn("⬅️ Image", "bprev_cyc_bg_prev", "none"), cbtn("Image ➡️", "bprev_cyc_bg_next", "none")])
    
    # Format-Specific Cyclers
    if fmt == "format3" and (len(chars) > 1 or c_char):
        buttons.append([cbtn("⬅️ Char", "bprev_cyc_char_prev", "none"), cbtn("Char ➡️", "bprev_cyc_char_next", "none")])
    if fmt == "format2" and (len(posters) > 1 or c_poster):
        buttons.append([cbtn("⬅️ Poster", "bprev_cyc_poster_prev", "none"), cbtn("Poster ➡️", "bprev_cyc_poster_next", "none")])
        
    # Logo Cycler
    logo_row = []
    if len(logos) > 1 or c_logo:
        logo_row.extend([cbtn("⬅️ Logo", "bprev_cyc_logo_prev", "none"), cbtn("Logo ➡️", "bprev_cyc_logo_next", "none")])
    if len(logos) > 0 or c_logo:
        logo_row.append(cbtn("❌ Drop Logo" if cache['show_logo'] else "✅ Add Logo", "bprev_cyc_logo_toggle", "none"))
        
    if logo_row:
        if len(logo_row) == 3: buttons.extend([logo_row[:2], [logo_row[2]]])
        else: buttons.append(logo_row)
            
    # Format Toggles
    buttons.append([
        cbtn("🎨 F1", "bprev_fmt_format1", "blue" if fmt == "format1" else "none"),
        cbtn("🎨 F2", "bprev_fmt_format2", "blue" if fmt == "format2" else "none"),
        cbtn("🎨 F3", "bprev_fmt_format3", "blue" if fmt == "format3" else "none"),
        cbtn("🎨 F4", "bprev_fmt_format4", "blue" if fmt == "format4" else "none")
    ])
    
    # Source Filters
    available = set(x['src'] for cat in cache['assets'].values() for x in cat)
    src_row = []
    for s in ['ALL', 'FanArt', 'TMDB', 'AniList', 'MAL', 'Kitsu']:
        if s in available or s == 'ALL':
            src_row.append(cbtn(f"✅ {s}" if src_filter == s else s, f"bprev_src_{s}", "none"))
    if len(src_row) > 3:
        buttons.extend([src_row[:3], src_row[3:]])
    elif src_row:
        buttons.append(src_row)
        
    buttons.append([cbtn("✅ Generate HD Document", "bprev_quality", "green")])
    buttons.append([cbtn("❌ Cancel", "bprev_cancel", "red")])
    
    caption = f"<blockquote expandable><b>🎨 Bᴀɴɴᴇʀ Pʀᴇᴠɪᴇᴡ Eᴅɪᴛᴏʀ</b></blockquote>\n<b>Anime:</b> <code>{cache['title']}</code>\n\nConfigure your banner using the buttons below.\n<i>Send any photo/URL to upload a custom asset!</i>"
    
    if msg_id_to_edit:
        try:
            await client.edit_message_media(
                chat_id=chat_id, message_id=msg_id_to_edit,
                media=InputMediaPhoto(out_path, caption=caption, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            cache['preview_msg_id'] = msg_id_to_edit
        except Exception:
            await client.delete_messages(chat_id, msg_id_to_edit)
            sent = await client.send_photo(chat_id, photo=out_path, caption=caption, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
            cache['preview_msg_id'] = sent.id
    else:
        sent = await client.send_photo(chat_id, photo=out_path, caption=caption, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
        cache['preview_msg_id'] = sent.id
        
    if status_msg: await status_msg.delete()
    if os.path.exists(out_path): os.remove(out_path)

# ==============================================================================
#                           EDITOR CALLBACKS
# ==============================================================================
@Client.on_callback_query(filters.regex(r"^bprev_cyc_(bg|char|logo|poster)_(prev|next|toggle)$") & admin)
async def bprev_cyc_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)
    
    atype, action = query.matches[0].groups()
    user_id = query.from_user.id
    
    if action == "toggle" and atype == "logo":
        cache['show_logo'] = not cache['show_logo']
    else:
        if atype in cache['custom']: del cache['custom'][atype]
        
        src_filter = cache['src_filter']
        l = cache['assets'].get(f"{atype}s", [])
        filtered = [x for x in l if x['src'] == src_filter] if src_filter != 'ALL' else l
        
        if filtered:
            if action == "next": cache['idx'][atype] += 1
            elif action == "prev": cache['idx'][atype] -= 1
            
    await query.answer("Rendering...")
    await render_banner_preview(client, query.message.chat.id, user_id, msg_id_to_edit=query.message.id)

@Client.on_callback_query(filters.regex(r"^bprev_fmt_(format1|format2|format3|format4)$") & admin)
async def bprev_fmt_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    fmt = query.matches[0].group(1)
    user_id = query.from_user.id
    cache['format'] = fmt
    await query.answer("Changing Format...")
    await render_banner_preview(client, query.message.chat.id, user_id, msg_id_to_edit=query.message.id)

@Client.on_callback_query(filters.regex(r"^bprev_src_(.+)$") & admin)
async def bprev_src_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    src = query.matches[0].group(1)
    user_id = query.from_user.id
    cache['src_filter'] = src
    cache['custom'] = {}
    await query.answer(f"Switched to {src}")
    await render_banner_preview(client, query.message.chat.id, user_id, msg_id_to_edit=query.message.id)

@Client.on_callback_query(filters.regex(r"^bprev_cancel$") & admin)
async def bprev_cancel_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    user_id = query.from_user.id
    del BANNER_CACHE[user_id]
    await query.message.delete()

@Client.on_callback_query(filters.regex(r"^bprev_back_editor$") & admin)
async def bprev_back_editor_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    user_id = query.from_user.id
    await render_banner_preview(client, query.message.chat.id, user_id, msg_id_to_edit=query.message.id)

# ==============================================================================
#                           FINAL HD RENDER
# ==============================================================================
@Client.on_callback_query(filters.regex(r"^bprev_quality$") & admin)
async def bprev_quality_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    q_kb = InlineKeyboardMarkup([
        [cbtn("HD (720p)", "bprev_render_1.0", "blue"), cbtn("FHD (1080p)", "bprev_render_1.5", "blue")], 
        [cbtn("QHD (2K)", "bprev_render_2.0", "blue"), cbtn("UHD (4K)", "bprev_render_3.0", "blue")], 
        [cbtn("⬅️ Back to Editor", "bprev_back_editor", "red")]
    ])
    await query.message.edit_reply_markup(reply_markup=q_kb)

@Client.on_callback_query(filters.regex(r"^bprev_render_(.+)$") & admin)
async def bprev_render_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    scale = float(query.matches[0].group(1))
    user_id = query.from_user.id
    cache['scale'] = scale
    
    await query.message.edit_caption("⏳ <code>Rendering Final HD Document...</code>", parse_mode=enums.ParseMode.HTML)
    
    src_filter = cache['src_filter']
    def get_filtered(atype):
        l = cache['assets'].get(f"{atype}s", [])
        return [x for x in l if x['src'] == src_filter] if src_filter != 'ALL' else l
        
    bgs = get_filtered('bg')
    chars = get_filtered('char')
    logos = get_filtered('logo')
    posters = get_filtered('poster')
    
    idx = cache['idx']
    c_bg = cache['custom'].get('bg')
    bg_url = c_bg if c_bg else (bgs[idx['bg'] % len(bgs)]['url'] if bgs else None)
    
    c_char = cache['custom'].get('char')
    char_url = c_char if c_char else (chars[idx['char'] % len(chars)]['url'] if chars else None)
    
    c_logo = cache['custom'].get('logo')
    logo_url = c_logo if c_logo else (logos[idx['logo'] % len(logos)]['url'] if logos and cache['show_logo'] else None)
    
    c_poster = cache['custom'].get('poster')
    poster_url = c_poster if c_poster else (posters[idx['poster'] % len(posters)]['url'] if posters else cache['data'].get('coverImage', {}).get('extraLarge'))
    
    fmt = cache['format']
    if fmt == "format2":
        char_url = poster_url
        
    format_mod = f"banner_{fmt}"
    try:
        mod = importlib.import_module(f"plugins.Element_Banner.{format_mod}")
    except Exception as e:
        return await query.message.edit_caption(f"❌ Error loading format: {e}")
        
    assets_for_render = {
        'bg': [bg_url, "API"] if bg_url else None,
        'char': [char_url, "API"] if char_url else None,
        'logo': [logo_url, "API"] if logo_url else None
    }
    
    patched_data = cache['data'].copy()
    if 'coverImage' not in patched_data: patched_data['coverImage'] = {}
    patched_data['coverImage']['extraLarge'] = poster_url
    
    out_path = os.path.join(DOWNLOAD_DIR, f"final_banner_{cache['a_id']}_{int(time.time())}.png")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    await asyncio.to_thread(mod.render_banner, patched_data, assets_for_render, scale, out_path)
    
    formats = await get_available_formats()
    regen_kb = build_formats_grid(formats, callback_prefix="bnregen_")
    
    final_caption = f"✅ <b>Banner Generated! ({format_mod})</b>\nAnime: <code>{cache['title']}</code>\n🌟 <b>Scale:</b> {scale}x\n\n👇 <b>Click a format to instantly re-generate with these assets!</b>"
    
    await client.send_document(query.message.chat.id, document=out_path, caption=final_caption, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(regen_kb))
    await query.message.delete()
    if os.path.exists(out_path): os.remove(out_path)

@Client.on_callback_query(filters.regex(r"^bnregen_(.+)$") & admin)
async def banner_regen_cb(client, query):
    cache = verify_session(query)
    if cache is None: return await query.answer("Session expired.", show_alert=True)
    if cache is False: return await query.answer("❌ This is not your session!", show_alert=True)

    format_id = query.matches[0].group(1)
    user_id = query.from_user.id
    fmt = format_id.replace('banner_', '')
    cache['format'] = fmt
    
    gen_msg = await query.message.reply(f"⏳ <code>Re-rendering {cache['title']} with {format_id}...</code>", parse_mode=enums.ParseMode.HTML)
    
    src_filter = cache['src_filter']
    def get_filtered(atype):
        l = cache['assets'].get(f"{atype}s", [])
        return [x for x in l if x['src'] == src_filter] if src_filter != 'ALL' else l
        
    bgs = get_filtered('bg')
    chars = get_filtered('char')
    logos = get_filtered('logo')
    posters = get_filtered('poster')
    
    idx = cache['idx']
    c_bg = cache['custom'].get('bg')
    bg_url = c_bg if c_bg else (bgs[idx['bg'] % len(bgs)]['url'] if bgs else None)
    
    c_char = cache['custom'].get('char')
    char_url = c_char if c_char else (chars[idx['char'] % len(chars)]['url'] if chars else None)
    
    c_logo = cache['custom'].get('logo')
    logo_url = c_logo if c_logo else (logos[idx['logo'] % len(logos)]['url'] if logos and cache['show_logo'] else None)
    
    c_poster = cache['custom'].get('poster')
    poster_url = c_poster if c_poster else (posters[idx['poster'] % len(posters)]['url'] if posters else cache['data'].get('coverImage', {}).get('extraLarge'))
    
    if fmt == "format2":
        char_url = poster_url
        
    try:
        mod = importlib.import_module(f"plugins.Element_Banner.{format_id}")
    except Exception as e:
        return await gen_msg.edit_text(f"❌ Failed to load format {format_id}: {e}")
        
    assets_for_render = {
        'bg': [bg_url, "API"] if bg_url else None,
        'char': [char_url, "API"] if char_url else None,
        'logo': [logo_url, "API"] if logo_url else None
    }
    
    patched_data = cache['data'].copy()
    if 'coverImage' not in patched_data: patched_data['coverImage'] = {}
    patched_data['coverImage']['extraLarge'] = poster_url
    
    out_path = os.path.join(DOWNLOAD_DIR, f"regen_{cache['a_id']}_{int(time.time())}.png")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    await asyncio.to_thread(mod.render_banner, patched_data, assets_for_render, cache.get('scale', 1.0), out_path)
    
    formats = await get_available_formats()
    regen_kb = build_formats_grid(formats, callback_prefix="bnregen_")
    
    final_caption = f"✅ <b>Banner Generated! ({format_id})</b>\nAnime: <code>{cache['title']}</code>\n🌟 <b>Scale:</b> {cache.get('scale', 1.0)}x\n\n👇 <b>Click a format to instantly re-generate with these assets!</b>"
    
    await client.send_document(query.message.chat.id, document=out_path, caption=final_caption, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(regen_kb))
    await gen_msg.delete()
    if os.path.exists(out_path): os.remove(out_path)

# ==============================================================================
#                           CUSTOM ASSET CATCHER
# ==============================================================================
@Client.on_message((filters.photo | filters.document | filters.text | filters.command("cancel")) & admin, group=1)
async def custom_asset_catcher(client, message):
    user_id = message.from_user.id
    if user_id not in BANNER_CACHE: return
    
    cache = BANNER_CACHE[user_id]
    if message.chat.id != cache.get('chat_id'): return
    cache['last_active'] = time.time()
    
    if message.text and is_cancel(message.text):
        del BANNER_CACHE[user_id]
        return await message.reply("✅ <b>Editor Closed.</b>", parse_mode=enums.ParseMode.HTML)

    url_or_path = None
    if message.text:
        if message.text.startswith("http://") or message.text.startswith("https://"):
            url_or_path = message.text.strip()
        else:
            return 
            
    if message.document and message.document.mime_type and not message.document.mime_type.startswith("image/"):
        return
        
    if message.photo or message.document:
        prog = await message.reply("⏳ <code>Downloading custom asset...</code>", parse_mode=enums.ParseMode.HTML)
        save_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
        os.makedirs(save_dir, exist_ok=True)
        try:
            url_or_path = await message.download(file_name=os.path.join(save_dir, f"custom_{int(time.time())}{'.jpg' if message.photo else ''}"))
            await prog.delete()
        except Exception as e:
            return await prog.edit_text(f"❌ <b>Download Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
        
    if url_or_path:
        kb = InlineKeyboardMarkup([
            [cbtn("🖼️ Set as Background", f"bprev_apply_bg_{user_id}", "blue")],
            [cbtn("👤 Set as Character", f"bprev_apply_char_{user_id}", "blue")],
            [cbtn("🔠 Set as Logo", f"bprev_apply_logo_{user_id}", "blue")],
            [cbtn("📜 Set as Poster", f"bprev_apply_poster_{user_id}", "blue")],
            [cbtn("❌ Cancel", f"bprev_apply_cancel_{user_id}", "red")]
        ])
        BANNER_CACHE[user_id]['temp_custom'] = url_or_path
        await message.reply("<blockquote><b>✨ Cᴜꜱᴛᴏᴍ Uᴘʟᴏᴀᴅ</b></blockquote>\nWhere do you want to inject this image into the layout?", reply_markup=kb, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^bprev_apply_(bg|char|logo|poster|cancel)_(\d+)$") & admin)
async def bprev_apply_cb(client, query):
    action = query.matches[0].group(1)
    owner_id = int(query.matches[0].group(2))
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your session!", show_alert=True)
        
    user_id = query.from_user.id
    if user_id not in BANNER_CACHE or 'temp_custom' not in BANNER_CACHE[user_id]:
        return await query.answer("Expired.", show_alert=True)
        
    if action == "cancel":
        await query.message.delete()
        return
        
    cache = BANNER_CACHE[user_id]
    cache['custom'][action] = cache['temp_custom']
    del cache['temp_custom']
    cache['last_active'] = time.time()
    
    await query.message.edit_text("✅ <b>Applied! Re-rendering preview...</b>", parse_mode=enums.ParseMode.HTML)
    await render_banner_preview(client, query.message.chat.id, user_id, msg_id_to_edit=cache.get('preview_msg_id'))
    await query.message.delete()
