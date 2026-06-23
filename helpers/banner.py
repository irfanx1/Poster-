"""
Banner generation logic.

This is intentionally a SIMPLE, working placeholder template (cover image +
gradient + title text) so the bot is fully functional out of the box. You
said you'll drop in your own banner design — this is the ONLY file you need
to edit to do that.

How to plug in your own design:
  1. Keep the function signature `generate_banner(poster_path, title,
     output_path) -> str` so plugins/generate.py doesn't need to change.
  2. Replace the body with your own PIL/Pillow drawing logic (custom
     layout, logo overlay, fonts, frames, gradients, watermark, etc).
  3. Drop any custom fonts into templates/fonts/ and point Config.FONT_PATH
     / FONT_PATH_BOLD at them.
  4. If you have a pre-made template PSD/PNG, load it as the base canvas
     instead of `Image.new(...)` below and composite the poster + title
     onto it.
"""

import os

from PIL import Image, ImageDraw, ImageFont

from config import Config


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def generate_banner(poster_path: str, title: str, output_path: str) -> str:
    W, H = Config.BANNER_WIDTH, Config.BANNER_HEIGHT
    canvas = Image.new("RGB", (W, H), (10, 10, 15))

    # --- background: cover image, scaled + cropped to fill the canvas ---
    poster = Image.open(poster_path).convert("RGB")
    ratio = poster.width / poster.height
    bg = poster.resize((W, max(H, int(W / ratio))))
    if bg.height < H:
        bg = poster.resize((max(W, int(H * ratio)), H))
    left = (bg.width - W) // 2
    top = (bg.height - H) // 2
    bg = bg.crop((left, top, left + W, top + H))
    canvas.paste(bg, (0, 0))

    # --- bottom gradient so the title text stays readable ---
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fade_start = int(H * 0.45)
    for y in range(fade_start, H):
        alpha = int(255 * ((y - fade_start) / (H - fade_start)) * 0.85)
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    # --- title text, auto-shrunk to fit width ---
    draw = ImageDraw.Draw(canvas)
    text = title.upper()
    size = 64
    font = _load_font(Config.FONT_PATH_BOLD, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    while tw > W - 80 and size > 24:
        size -= 4
        font = _load_font(Config.FONT_PATH_BOLD, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]

    tx = (W - tw) // 2
    ty = H - 140
    draw.text((tx + 3, ty + 3), text, font=font, fill=(0, 0, 0))   # shadow
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255))     # text

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    canvas.save(output_path, quality=95)
    return output_path
