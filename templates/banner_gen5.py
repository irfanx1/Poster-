import os
import math
import textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

from plugins.Element_Banner.banner_genlogic import (
    font, fetch_img, paste, ensure_fallback,
    fmt_num, TRANS, WHITE, WHITE_DIM
)

FORMAT_NAME = "Element Vox (Maroon Landscape)"
PREVIEW_URL = "https://i.ibb.co/6H8f93S/maroon-landscape-format.png" # You can update this preview URL

# ─── COLOURS & CONSTANTS ──────────────────────────────────────────────────────
BG_COLOR         = (22, 4, 7, 255)
CARD_COLOR       = (28, 10, 14, 215)
SIDEBAR_COLOR    = (26, 8, 12, 225)
TAG_OUTLINE      = (255, 255, 255, 180)
TAG_FILL         = (255, 255, 255, 15)
TEXT_LIGHT       = (210, 200, 205, 230)
ACCENT_RED       = (210, 28, 28, 255)
SECTION_HEADING  = (255, 255, 255, 255)

# ─── GEOMETRIC ICONS ─────────────────────────────────────────────────────────
def draw_house_icon(draw, cx, cy, size, color):
    h, w = size, size
    draw.polygon([(cx, cy - h // 2), (cx - w // 2, cy), (cx + w // 2, cy)], fill=color)
    draw.rectangle([(cx - w // 4, cy), (cx + w // 4, cy + h // 2)], fill=color)
    draw.rectangle([(cx - w // 2 + 2, cy), (cx + w // 2 - 2, cy + h // 2)], fill=color)

def draw_search_icon(draw, cx, cy, size, color):
    r, lw = int(size * 0.38), max(2, size // 9)
    draw.ellipse([(cx - r - 4, cy - r - 4), (cx + r - 4, cy + r - 4)], outline=color, width=lw)
    hx1, hy1 = cx - 4 + int(r * math.cos(math.pi/4)), cy - 4 + int(r * math.sin(math.pi/4))
    draw.line([(hx1, hy1), (hx1 + int(size * 0.32), hy1 + int(size * 0.32))], fill=color, width=lw)

def draw_list_icon(draw, cx, cy, size, color):
    bar_w, bar_h, gap = int(size * 0.65), max(2, size // 9), size // 4
    x1 = cx - bar_w // 2
    for dy in [-gap, 0, gap]:
        draw.rectangle([(x1, cy + dy - bar_h // 2), (x1 + bar_w, cy + dy + bar_h // 2)], fill=color)

def draw_star_icon(draw, cx, cy, size, color):
    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size // 2 if i % 2 == 0 else size // 4
        pts.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
    draw.polygon(pts, fill=color)

# ─── SHAPE HELPERS ───────────────────────────────────────────────────────────
def draw_card_with_shadow(canvas, draw, xy, radius, fill):
    """Draws an ultra-smooth card with a Gaussian drop shadow."""
    x1, y1, x2, y2 = xy
    # Shadow layer
    shadow = Image.new('RGBA', canvas.size, TRANS)
    shad_draw = ImageDraw.Draw(shadow)
    
    # Try safe rounded rect
    try:
        shad_draw.rounded_rectangle((x1+4, y1+4, x2+4, y2+4), radius=radius, fill=(0,0,0,180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        canvas.alpha_composite(shadow)
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill)
    except AttributeError:
        # Fallback for older PIL
        draw.rectangle([(x1, y1), (x2, y2)], fill=fill)

def get_text_width(fnt, text):
    try: return fnt.getlength(text)
    except AttributeError:
        try: return fnt.getsize(text)[0]
        except AttributeError: return len(text) * (fnt.size // 2)

def wrap_text_safe(text, fnt, max_px):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if get_text_width(fnt, test) <= max_px: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def _split_title(title, max_chars=14):
    words, lines, cur = title.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if len(test) <= max_chars or not cur: cur = test
        else:
            lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines[:4]

# ─── MAIN RENDERER ───────────────────────────────────────────────────────────
def render_banner(data, assets, scale, out_path):
    def S(v): return int(v * scale)

    CW, CH = S(1280), S(720)
    
    # Data extraction
    title = data["title"].get("english") or data["title"].get("romaji") or "Unknown"
    desc = data.get("description", "No synopsis available.").replace("<br>", "\n").replace("<i>", "").replace("</i>", "")
    
    # Prioritize landscape background
    bg_url = assets['bg'][0] if assets and assets.get('bg') else data.get('coverImage', {}).get('extraLarge')
    bg_img = fetch_img(bg_url) if bg_url else fetch_img(ensure_fallback())
    
    logo_url = assets['logo'][0] if assets and assets.get('logo') else None
    logo_img = fetch_img(logo_url) if logo_url else None
    
    canvas = Image.new("RGBA", (CW, CH), BG_COLOR)

    # 1. ─── REFINED MAROON BACKGROUND ───
    if bg_img:
        bg = bg_img.convert("RGBA")
        sc = max(CW / bg.width, CH / bg.height)
        nw, nh = int(bg.width * sc), int(bg.height * sc)
        bg = bg.resize((nw, nh), Image.LANCZOS)
        cx, cy = (nw - CW) // 2, (nh - CH) // 2
        bg = bg.crop((cx, cy, cx + CW, cy + CH))

        # Desaturate and darken
        bg_rgb = ImageEnhance.Color(bg.convert("RGB")).enhance(0.55)
        bg_rgb = ImageEnhance.Brightness(bg_rgb).enhance(0.35)
        
        tint = Image.new("RGB", (CW, CH), (22, 4, 7))
        bg_tinted = Image.blend(tint, bg_rgb, 0.45).convert("RGBA")

        # Smooth left-to-right fade mask
        mask = Image.new("L", (CW, CH), 0)
        md = ImageDraw.Draw(mask)
        fade_start, fade_end = int(CW * 0.28), int(CW * 0.55)
        md.rectangle([(fade_end, 0), (CW, CH)], fill=200)
        for x in range(fade_start, fade_end):
            alpha = int(200 * ((x - fade_start) / (fade_end - fade_start)) ** 1.5)
            md.line([(x, 0), (x, CH)], fill=alpha)

        bg_layer = Image.new("RGBA", (CW, CH), TRANS)
        bg_layer.paste(bg_tinted, (0, 0), mask)
        canvas.alpha_composite(bg_layer)

    draw = ImageDraw.Draw(canvas)

    # 2. ─── TOP BAR ───
    canvas.alpha_composite(Image.new("RGBA", (CW, S(80)), (0, 0, 0, 50)))
    draw.text((S(28), S(26)), "☰", font=font(S(26), "bold"), fill=WHITE)
    draw.text((S(68), S(22)), "ELEMENT VOX", font=font(S(32), "bold"), fill=WHITE)

    # 3. ─── SIDEBAR PANEL ───
    SB_X, SB_Y, SB_W, SB_H = S(5), S(118), S(88), S(572)
    SB_ICON_CX = SB_X + SB_W // 2
    
    draw_card_with_shadow(canvas, draw, (SB_X, SB_Y, SB_X+SB_W, SB_Y+SB_H), S(16), SIDEBAR_COLOR)

    nav_items = [(draw_house_icon, "HOME", True), (draw_search_icon, "SEARCH", False),
                 (draw_list_icon, "CATEGORY", False), (draw_star_icon, "RATING", False)]
    f_nav_lbl = font(S(10), "bold")
    item_spacing = SB_H // len(nav_items)

    for idx, (icon_fn, label, active) in enumerate(nav_items):
        i_col = ACCENT_RED if active else (200, 190, 195, 210)
        item_cy = SB_Y + idx * item_spacing + item_spacing // 2
        icon_fn(draw, SB_ICON_CX, item_cy - S(10), S(28), i_col)
        lw = get_text_width(f_nav_lbl, label)
        draw.text((SB_ICON_CX - lw // 2, item_cy + S(14)), label, font=f_nav_lbl, fill=i_col)

    # 4. ─── GENRE PILLS ───
    TAG_X, TAG_Y, TAG_H = S(138), S(118), S(36)
    f_tag = font(S(12), "bold")
    tx = TAG_X
    
    genres = data.get("genres", ["ACTION", "DRAMA"])[:4]
    for genre in genres:
        label = genre.upper()
        pw = get_text_width(f_tag, label) + S(36)
        
        pill = Image.new("RGBA", (int(pw), int(TAG_H)), TRANS)
        pd = ImageDraw.Draw(pill)
        try: pd.rounded_rectangle([(0,0), (pw-1, TAG_H-1)], radius=S(18), fill=TAG_FILL, outline=TAG_OUTLINE, width=S(2))
        except: pd.rectangle([(0,0), (pw-1, TAG_H-1)], fill=TAG_FILL, outline=TAG_OUTLINE, width=S(2))
        paste(canvas, pill, (tx, TAG_Y))
        
        draw.text((tx + S(18), TAG_Y + S(9)), label, font=f_tag, fill=WHITE)
        tx += pw + S(12)

    # 5. ─── TITLE / LOGO CARD ───
    TC_X, TC_Y, TC_W, TC_H = S(138), S(170), S(648), S(215)
    draw_card_with_shadow(canvas, draw, (TC_X, TC_Y, TC_X+TC_W, TC_Y+TC_H), S(14), CARD_COLOR)

    if logo_img:
        # Dynamic Logo Switcher
        lw, lh = logo_img.size
        sc = min((TC_W - S(60)) / lw, (TC_H - S(40)) / lh)
        lw2, lh2 = int(lw * sc), int(lh * sc)
        logo_img = logo_img.resize((lw2, lh2), Image.LANCZOS)
        
        lx = TC_X + (TC_W - lw2) // 2
        ly = TC_Y + (TC_H - lh2) // 2
        paste(canvas, logo_img, (lx, ly))
    else:
        # Fallback Text Title
        title_lines = _split_title(title.upper(), max_chars=13)
        fs = S(90)
        f_title = font(fs, "black")
        while fs > S(40):
            f_title = font(fs, "black")
            if max([get_text_width(f_title, l) for l in title_lines]) <= TC_W - S(60): break
            fs -= S(4)
            
        ty = TC_Y + (TC_H - len(title_lines) * (fs + S(6))) // 2
        for line in title_lines:
            draw.text((TC_X + S(30), ty), line, font=f_title, fill=WHITE)
            ty += fs + S(6)

    # 6. ─── INFO CARD ───
    IC_X, IC_Y, IC_W, IC_H = S(138), S(398), S(648), S(270)
    draw_card_with_shadow(canvas, draw, (IC_X, IC_Y, IC_X+IC_W, IC_Y+IC_H), S(14), CARD_COLOR)

    PAD_L = IC_X + S(35)
    f_info_hdr = font(S(15), "bold")
    f_info_item = font(S(14), "medium")
    f_info_val = font(S(14), "bold")

    draw.text((PAD_L, IC_Y + S(28)), "INFORMATION", font=f_info_hdr, fill=SECTION_HEADING)

    info_items = [
        ("RELEASE", data.get("startDate", {}).get("year", "N/A")),
        ("STATUS", data.get("status", "N/A")),
        ("RATINGS", f"{data.get('averageScore', 0)/10:.1f}/10" if data.get('averageScore') else "N/A"),
        ("POPULARITY", f"{fmt_num(data.get('popularity', 0))}+" if data.get('popularity') else "N/A"),
    ]

    iy = IC_Y + S(68)
    for label, value in info_items:
        draw.ellipse([(PAD_L, iy + S(7)), (PAD_L + S(8), iy + S(15))], fill=WHITE)
        lbl_text = f"{label} : "
        draw.text((PAD_L + S(18), iy), lbl_text, font=f_info_item, fill=TEXT_LIGHT)
        lx = PAD_L + S(18) + get_text_width(f_info_item, lbl_text)
        draw.text((lx, iy), str(value), font=f_info_val, fill=WHITE)
        iy += S(38)

    # 7. ─── FEATURED CARD (LANDSCAPE) ───
    FC_X, FC_Y, FC_W, FC_H = S(818), S(118), S(425), S(353)
    draw_card_with_shadow(canvas, draw, (FC_X, FC_Y, FC_X+FC_W, FC_Y+FC_H), S(14), CARD_COLOR)

    THUMB_PAD = S(16)
    TW, TH = FC_W - THUMB_PAD * 2, S(180) # Force Landscape Thumbnail
    
    if bg_img:
        # Mathematically centre-crop the background to fit the landscape feature box
        thumb = ImageOps.fit(bg_img.convert("RGBA"), (TW, TH), Image.LANCZOS)
        
        # Round the inner image corners for a smoother texture
        mask = Image.new("L", (TW, TH), 0)
        try: ImageDraw.Draw(mask).rounded_rectangle((0,0, TW, TH), radius=S(8), fill=255)
        except: ImageDraw.Draw(mask).rectangle((0,0, TW, TH), fill=255)
        thumb.putalpha(mask)
        
        paste(canvas, thumb, (FC_X + THUMB_PAD, FC_Y + THUMB_PAD))

    f_card_hdr = font(S(14), "bold")
    f_card_txt = font(S(12), "bold") # Small Caps Style
    
    feat_hdr_y = FC_Y + THUMB_PAD + TH + S(14)
    draw.text((FC_X + THUMB_PAD, feat_hdr_y), "FEATURED", font=f_card_hdr, fill=SECTION_HEADING)

    # Synopsis splitting engine
    desc_lines = wrap_text_safe(desc.upper(), f_card_txt, FC_W - THUMB_PAD * 2)
    feat_text_y = feat_hdr_y + S(24)
    
    feat_line_count = int((FC_Y + FC_H - feat_text_y - S(10)) // S(19))
    
    for line in desc_lines[:feat_line_count]:
        draw.text((FC_X + THUMB_PAD, feat_text_y), line, font=f_card_txt, fill=TEXT_LIGHT)
        feat_text_y += S(19)

    # 8. ─── OVERVIEW CARD ───
    OV_X, OV_Y, OV_W, OV_H = S(818), S(484), S(425), S(198)
    draw_card_with_shadow(canvas, draw, (OV_X, OV_Y, OV_X+OV_W, OV_Y+OV_H), S(14), CARD_COLOR)

    ov_hdr_y = OV_Y + S(22)
    draw.text((OV_X + THUMB_PAD, ov_hdr_y), "OVERVIEW", font=f_card_hdr, fill=SECTION_HEADING)

    ov_text_y = ov_hdr_y + S(24)
    ov_line_count = int((OV_Y + OV_H - ov_text_y - S(12)) // S(19))
    
    remaining_lines = desc_lines[feat_line_count:]
    for i, line in enumerate(remaining_lines[:ov_line_count]):
        if i == ov_line_count - 1 and len(remaining_lines) > ov_line_count:
            line = line[:-3] + "..." # Truncate if overflowing overview
        draw.text((OV_X + THUMB_PAD, ov_text_y), line, font=f_card_txt, fill=TEXT_LIGHT)
        ov_text_y += S(19)

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path
