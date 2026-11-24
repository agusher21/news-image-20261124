#!/usr/bin/env python3
"""
news-image-20261124 round 2 generator — FIXED
Produces out/entry.png — 1024x1024 RGB PNG, <= 1 MiB
All overlaps resolved, density tightened, scenes clipped to panels.
"""
from __future__ import annotations
import os
import sys
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Constants ──────────────────────────────────────────────────────────────
W, H = 1024, 1024
CREAM = (245, 240, 225)
RED = (192, 57, 43)
NAVY = (26, 26, 46)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (60, 60, 60)
MED_GRAY = (100, 100, 100)

REGION_COLOURS = {
    "EUROPE": (200, 30, 30),
    "MIDDLE EAST": (220, 120, 30),
    "ASIA-PACIFIC": (30, 140, 80),
    "AMERICAS": (30, 90, 180),
    "AFRICA": (160, 90, 30),
    "OCEANIA": (100, 60, 160),
    "WORLD": (80, 80, 80),
}

TAG_COLOURS = {
    "ONGOING": (200, 180, 40),
    "REPORTED": (40, 140, 200),
    "CLAIM": (180, 60, 180),
    "OFFICIALS SAY": (60, 180, 100),
}

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
SERIF_BOLD = FONT_DIR / "DejaVuSerif-Bold.ttf"
SERIF = FONT_DIR / "DejaVuSerif.ttf"
SANS = FONT_DIR / "DejaVuSans.ttf"
SANS_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
MONO = FONT_DIR / "DejaVuSansMono.ttf"

def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)

F_TITLE = load_font(SERIF_BOLD, 36)
F_SUBHEAD = load_font(SERIF, 17)
F_HEADLINE = load_font(SERIF_BOLD, 26)
F_HEADLINE_SM = load_font(SERIF_BOLD, 20)
F_HEADLINE_XS = load_font(SERIF_BOLD, 17)
F_BODY = load_font(SANS, 13)
F_BODY_SM = load_font(SANS, 11)
F_BODY_XS = load_font(SANS, 9)
F_CAPTION = load_font(SANS, 10)
F_CAPTION_BOLD = load_font(SANS_BOLD, 10)
F_STAT_NUM = load_font(SERIF_BOLD, 20)  # shrunk for clearance
F_STAT_LBL = load_font(SANS, 8)
F_TAB = load_font(SANS_BOLD, 9)
F_TIMELINE = load_font(SANS_BOLD, 9)
F_TIMELINE_EVT = load_font(SANS, 8)
F_MAP_NUM = load_font(SANS_BOLD, 9)
F_LEGEND = load_font(SANS, 8)
F_FOOTER = load_font(SANS, 9)

MARGIN = 12
CONTENT_W = W - 2 * MARGIN

# ─── Helpers ────────────────────────────────────────────────────────────────
def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def font_ascent(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    return font.getmetrics()[0]

def font_descent(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    return font.getmetrics()[1]

def font_height(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    a, d = font.getmetrics()
    return a + d

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        tw, _ = measure_text(draw, test, font)
        if tw <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_text_box(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont,
                  color: tuple, max_w: int, line_spacing: int = 1, align: str = "left", max_lines: int = None,
                  no_ellipsis: bool = False) -> int:
    lines = wrap_text(draw, text, font, max_w)
    if max_lines is not None and len(lines) > max_lines:
        if no_ellipsis:
            raise ValueError(f"Text exceeds max_lines={max_lines} and no_ellipsis=True: {text!r}")
        lines = lines[:max_lines]
        last = lines[-1]
        while measure_text(draw, last + "…", font)[0] > max_w and len(last) > 3:
            last = last[:-1]
        lines[-1] = last + "…"
    h = 0
    for line in lines:
        tw, th = measure_text(draw, line, font)
        if align == "center":
            tx = x + (max_w - tw) // 2
        elif align == "right":
            tx = x + max_w - tw
        else:
            tx = x
        draw.text((tx, y + h), line, font=font, fill=color)
        h += th + line_spacing
    return h


def draw_text_clipped(draw: ImageDraw.ImageDraw, img: Image.Image, x: int, y: int, text: str,
                      font: ImageFont.FreeTypeFont, color: tuple, clip_w: int, max_lines: int = 1) -> int:
    """Draw text clipped to clip_w width by rendering on temp surface and pasting."""
    # First, prepare the text (wrap/truncate)
    temp_draw = ImageDraw.Draw(img)
    lines = wrap_text(temp_draw, text, font, clip_w)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while measure_text(temp_draw, last + "…", font)[0] > clip_w and len(last) > 3:
            last = last[:-1]
        lines[-1] = last + "…"
    
    # Render each line on a temp RGBA image, then paste clipped
    total_h = 0
    for line in lines:
        tw, th = measure_text(temp_draw, line, font)
        # Create temp image for this line
        line_img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        line_draw = ImageDraw.Draw(line_img)
        line_draw.text((0, 0), line, font=font, fill=color + (255,))
        # Clip to clip_w
        if tw > clip_w:
            line_img = line_img.crop((0, 0, clip_w, th))
        # Paste onto main image
        img.paste(line_img, (x, y + total_h), line_img)
        total_h += th
    print(f"DEBUG CLIPPED: x={x}, y={y}, clip_w={clip_w}, lines={lines}, total_h={total_h}")
    return total_h

def draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont,
              bg: tuple, fg: tuple = WHITE, pad_x: int = 5, pad_y: int = 2, radius: int = 3) -> tuple[int, int]:
    tw, th = measure_text(draw, text, font)
    w = tw + 2 * pad_x
    h = th + 2 * pad_y
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg)
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=fg)
    return w, h

# ─── Scene drawing WITH CLIPPING ────────────────────────────────────────────
def draw_dawn_sky(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    for i in range(h):
        t = i / h
        r = int(255 * (1 - t * 0.3))
        g = int(215 * (1 - t * 0.4) + 240 * t * 0.4)
        b = int(60 * (1 - t * 0.8) + 220 * t * 0.8)
        draw.line([(x, y + i), (x + w, y + i)], fill=(r, g, b))

def draw_noon_sky(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    for i in range(h):
        t = i / h
        r = int(135 * (1 - t * 0.3) + 200 * t * 0.3)
        g = int(206 * (1 - t * 0.2) + 230 * t * 0.2)
        b = int(250 * (1 - t * 0.1) + 255 * t * 0.1)
        draw.line([(x, y + i), (x + w, y + i)], fill=(r, g, b))

def draw_night_sky(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    draw.rectangle([x, y, x + w, y + h], fill=(10, 10, 30))
    random.seed(42)
    for _ in range(60):
        sx = x + random.randint(0, w - 1)
        sy = y + random.randint(0, h - 1)
        size = random.choice([1, 1, 1, 2, 2, 3])
        brightness = random.randint(180, 255)
        draw.ellipse([sx, sy, sx + size, sy + size], fill=(brightness, brightness, brightness))

def draw_nvidia_hq(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    ground_y = y + h - 20
    draw.line([(x, ground_y), (x + w, ground_y)], fill=(80, 70, 50), width=3)
    tower_w = min(60, w // 3)
    tower_x = x + (w - tower_w) // 2
    tower_h = h - 40
    tower_y = y + h - tower_h - 20
    pane_h = 14
    pane_gap = 3
    for i in range(tower_h // (pane_h + pane_gap)):
        py = tower_y + i * (pane_h + pane_gap)
        if i % 2 == 0:
            color = (180, 200, 230, 200)
        else:
            color = (100, 130, 170, 200)
        draw.rectangle([tower_x + 2, py, tower_x + tower_w - 2, py + pane_h], fill=color, outline=(80, 100, 130))
    draw.rectangle([tower_x, tower_y, tower_x + tower_w, tower_y + tower_h], outline=(60, 80, 100), width=2)
    sun_cx = x + w // 2
    sun_cy = tower_y - 10
    for r in range(28, 0, -1):
        blend = int(255 * (1 - r / 28) * 0.6)
        color = (255, 215 + blend // 3, 60 + blend // 2)
        draw.ellipse([sun_cx - r, sun_cy - r, sun_cx + r, sun_cy + r], outline=color, width=1)
    draw.ellipse([sun_cx - 12, sun_cy - 12, sun_cx + 12, sun_cy + 12], fill=(255, 230, 100))
    for px in [x + 10, x + w - 25]:
        draw.line([(px + 12, ground_y), (px + 14, ground_y - 45)], fill=(40, 30, 20), width=4)
        draw.line([(px + 14, ground_y - 45), (px + 16, ground_y - 40)], fill=(40, 30, 20), width=3)
        for angle in [-50, -30, -10, 10, 30, 50]:
            rad = math.radians(angle)
            fx = px + 14 + int(28 * math.sin(rad))
            fy = ground_y - 45 - int(28 * math.cos(rad))
            draw.line([(px + 14, ground_y - 45), (fx, fy)], fill=(30, 70, 30), width=2)

def draw_london_hospital(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    bx, by = x + 15, y + h - 100
    bw, bh = w - 30, 85
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(245, 245, 245), outline=(150, 150, 150), width=2)
    for wx in range(bx + 10, bx + bw - 10, 20):
        for wy in range(by + 10, by + bh - 10, 18):
            draw.rectangle([wx, wy, wx + 12, wy + 12], fill=(200, 220, 240), outline=(180, 180, 180))
    cx, cy = bx + bw // 2, by - 8
    draw.rectangle([cx - 10, cy - 4, cx + 10, cy + 4], fill=RED)
    draw.rectangle([cx - 4, cy - 10, cx + 4, cy + 4], fill=RED)
    ax, ay = bx - 20, by + bh - 20
    draw.rectangle([ax, ay, ax + 30, ay + 14], fill=WHITE, outline=(100, 100, 100), width=1)
    draw.rectangle([ax + 3, ay + 1, ax + 10, ay + 10], fill=RED)
    draw.rectangle([ax + 17, ay + 1, ax + 24, ay + 10], fill=RED)
    draw.ellipse([ax + 3, ay + 12, ax + 9, ay + 18], fill=(30, 30, 30))
    draw.ellipse([ax + 21, ay + 12, ax + 27, ay + 18], fill=(30, 30, 30))
    bbx = x + w - 35
    bby = by + bh
    draw.rectangle([bbx, bby - 65, bbx + 22, bby], fill=(40, 40, 60))
    draw.rectangle([bbx + 3, bby - 80, bbx + 19, bby - 65], fill=(40, 40, 60))
    draw.ellipse([bbx + 3, bby - 90, bbx + 19, bby - 73], fill=(40, 40, 60))

def draw_orbit_scene(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
    """Earth limb and satellite, clipped to panel scene rect — DARK BLUE LIMB."""
    earth_r = min(w, h) // 2 + 10
    extra = earth_r - 5
    layer_h = h + extra
    layer = Image.new("RGBA", (w, layer_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    earth_cx = w // 2
    earth_cy = h - 5

    # DARK BLUE limb — thick filled band (not thin arc)
    # Draw multiple concentric arcs to create a 12px thick limb band
    for r in range(earth_r, earth_r - 12, -1):
        # Dark navy gradient - darker at top (space), lighter at bottom (atmosphere)
        t = (earth_r - r) / 12
        r_col = int(5 * (1 - t) + 15 * t)
        g_col = int(15 * (1 - t) + 40 * t)
        b_col = int(60 * (1 - t) + 100 * t)
        ld.arc([earth_cx - r, earth_cy - r, earth_cx + r, earth_cy + r],
               start=180, end=360, fill=(r_col, g_col, b_col), width=2)

    # Atmosphere glow - thin bright blue line at top of limb
    glow_r = earth_r - 12
    ld.arc([earth_cx - glow_r, earth_cy - glow_r, earth_cx + glow_r, earth_cy + glow_r],
           start=180, end=360, fill=(60, 120, 200), width=1)

    # Satellite in upper portion of scene
    sat_x, sat_y = w // 2, h // 3
    ld.rectangle([sat_x - 10, sat_y - 6, sat_x + 10, sat_y + 6], fill=(80, 80, 90), outline=(120, 120, 130), width=2)
    ld.rectangle([sat_x - 35, sat_y - 5, sat_x - 12, sat_y + 5], fill=(30, 30, 50), outline=(60, 60, 80), width=1)
    ld.rectangle([sat_x + 12, sat_y - 5, sat_x + 35, sat_y + 5], fill=(30, 30, 50), outline=(60, 60, 80), width=1)
    for px in range(sat_x - 33, sat_x - 13, 7):
        ld.line([(px, sat_y - 4), (px, sat_y + 4)], fill=(40, 40, 70), width=1)
    for px in range(sat_x + 13, sat_x + 33, 7):
        ld.line([(px, sat_y - 4), (px, sat_y + 4)], fill=(40, 40, 70), width=1)
    ld.line([(sat_x, sat_y - 6), (sat_x, sat_y - 16)], fill=(100, 100, 110), width=2)
    ld.ellipse([sat_x - 2, sat_y - 19, sat_x + 2, sat_y - 15], fill=(150, 150, 160))
    ld.ellipse([sat_x - 5, sat_y - 3, sat_x + 5, sat_y + 3], outline=(255, 200, 0), width=1)
    for angle in [90, 210, 330]:
        rad = math.radians(angle)
        x1 = sat_x + int(4 * math.cos(rad))
        y1 = sat_y + int(4 * math.sin(rad))
        x2 = sat_x + int(7 * math.cos(rad))
        y2 = sat_y + int(7 * math.sin(rad))
        ld.line([(x1, y1), (x2, y2)], fill=(255, 200, 0), width=2)

    scene_layer = layer.crop((0, 0, w, h))
    # Return the layer for the caller to composite — don't reference external img
    return scene_layer

# ─── Mini illustrations (fixed: no stray "00", no cross-card arrows) ────────
def draw_mini_illustration(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, idx: int):
    cx, cy = x + w // 2, y + h // 2
    if idx == 4:  # Armenia - document
        draw.rectangle([cx - 10, cy - 8, cx + 10, cy + 8], outline=NAVY, width=2)
        draw.line([(cx - 5, cy - 3), (cx + 5, cy - 3)], fill=NAVY, width=1)
        draw.line([(cx - 5, cy + 1), (cx + 5, cy + 1)], fill=NAVY, width=1)
        draw.line([(cx - 5, cy + 5), (cx + 1, cy + 5)], fill=NAVY, width=1)
    elif idx == 5:  # UN - globe
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=NAVY, width=2)
        draw.line([(cx, cy - 8), (cx, cy + 8)], fill=NAVY, width=1)
        draw.arc([cx - 8, cy - 8, cx + 8, cy + 8], start=0, end=180, fill=NAVY, width=1)
        draw.arc([cx - 8, cy - 8, cx + 8, cy + 8], start=180, end=360, fill=NAVY, width=1)
    elif idx == 6:  # Poland - meteor/arrow (contained)
        draw.line([(cx - 8, cy + 4), (cx + 8, cy - 4)], fill=RED, width=2)
        draw.polygon([(cx + 8, cy - 4), (cx + 11, cy - 1), (cx + 8, cy + 2)], fill=RED)
    elif idx == 7:  # Pakistan - seismic wave
        draw.line([(cx - 10, cy), (cx - 5, cy - 5), (cx, cy + 4), (cx + 5, cy - 6), (cx + 10, cy)], fill=RED, width=2)
    elif idx == 8:  # Nepal - mountains
        draw.polygon([(cx - 10, cy + 5), (cx - 3, cy - 7), (cx + 3, cy + 5)], fill=(180, 180, 180), outline=NAVY)
        draw.polygon([(cx - 3, cy + 5), (cx + 3, cy - 9), (cx + 10, cy + 5)], fill=(160, 160, 160), outline=NAVY)
    elif idx == 9:  # Panama - canal
        draw.line([(cx - 5, cy + 7), (cx - 5, cy - 7)], fill=NAVY, width=2)
        draw.line([(cx - 5, cy - 7), (cx + 1, cy - 10)], fill=NAVY, width=2)
        draw.line([(cx + 1, cy - 10), (cx + 5, cy - 3)], fill=NAVY, width=2)
    elif idx == 10:  # Germany - factory/@
        draw.rectangle([cx - 7, cy - 5, cx + 7, cy + 5], outline=NAVY, width=2)
        draw.line([(cx - 3, cy - 1), (cx + 3, cy - 1)], fill=NAVY, width=1)
        draw.line([(cx - 3, cy + 2), (cx + 3, cy + 2)], fill=NAVY, width=1)
        draw.text((cx - 3, cy - 6), "@", font=F_BODY_XS, fill=RED)
    elif idx == 11:  # Russia - Kremlin domes (FIXED: no "00" — single centered dome)
        # Single onion dome centered, no pair that looks like "00"
        draw.ellipse([cx - 7, cy - 10, cx + 7, cy + 4], outline=NAVY, width=2)
        draw.ellipse([cx - 7, cy - 14, cx + 7, cy - 10], fill=(180, 50, 50), outline=NAVY)
        draw.line([(cx - 7, cy - 10), (cx + 7, cy - 10)], fill=NAVY, width=2)
        # Cross on top
        draw.line([(cx, cy - 14), (cx, cy - 18)], fill=NAVY, width=2)
        draw.line([(cx - 3, cy - 16), (cx + 3, cy - 16)], fill=NAVY, width=2)
    elif idx == 12:  # Culture - theater masks
        draw.line([(cx, cy - 9), (cx, cy + 5)], fill=NAVY, width=2)
        draw.ellipse([cx - 6, cy - 1, cx + 1, cy + 7], fill=NAVY)
        draw.ellipse([cx + 1, cy - 6, cx + 8, cy + 2], fill=NAVY)
    elif idx == 13:  # China - flag/building
        draw.rectangle([cx - 8, cy - 9, cx + 8, cy + 9], outline=NAVY, width=2)
        draw.rectangle([cx - 5, cy - 5, cx + 5, cy], fill=RED)
        draw.line([(cx - 3, cy + 2), (cx + 3, cy + 2)], fill=NAVY, width=1)
        draw.line([(cx - 3, cy + 5), (cx + 3, cy + 5)], fill=NAVY, width=1)

# ─── Dotted world map ───────────────────────────────────────────────────────
LAND_GRID = [
    (-125, 50), (-115, 50), (-105, 50), (-95, 50), (-85, 50), (-75, 50),
    (-125, 40), (-115, 40), (-105, 40), (-95, 40), (-85, 40), (-75, 40),
    (-125, 30), (-115, 30), (-105, 30), (-95, 30), (-85, 30), (-75, 30),
    (-80, 25), (-70, 25), (-60, 25),
    (-80, 10), (-70, 10), (-60, 10), (-50, 10),
    (-80, 0), (-70, 0), (-60, 0), (-50, 0),
    (-70, -10), (-60, -10), (-50, -10),
    (-60, -20), (-50, -20), (-45, -20),
    (-55, -30), (-50, -30), (-45, -30),
    (-55, -40), (-50, -40),
    (-10, 60), (0, 60), (10, 60), (20, 60), (30, 60),
    (-10, 50), (0, 50), (10, 50), (20, 50), (30, 50), (40, 50),
    (-10, 40), (0, 40), (10, 40), (20, 40), (30, 40),
    (-20, 30), (-10, 30), (0, 30), (10, 30), (20, 30), (30, 30), (40, 30),
    (-20, 20), (-10, 20), (0, 20), (10, 20), (20, 20), (30, 20), (40, 20),
    (-20, 10), (-10, 10), (0, 10), (10, 10), (20, 10), (30, 10), (40, 10),
    (-20, 0), (-10, 0), (0, 0), (10, 0), (20, 0), (30, 0), (40, 0),
    (-10, -10), (0, -10), (10, -10), (20, -10), (30, -10),
    (10, -20), (20, -20), (30, -20), (40, -20),
    (20, -30), (30, -30), (40, -30),
    (30, 60), (40, 60), (50, 60), (60, 60), (70, 60), (80, 60), (90, 60), (100, 60), (110, 60), (120, 60), (130, 60), (140, 60),
    (30, 50), (40, 50), (50, 50), (60, 50), (70, 50), (80, 50), (90, 50), (100, 50), (110, 50), (120, 50), (130, 50), (140, 50),
    (30, 40), (40, 40), (50, 40), (60, 40), (70, 40), (80, 40), (90, 40), (100, 40), (110, 40), (120, 40), (130, 40),
    (40, 30), (50, 30), (60, 30), (70, 30), (80, 30), (90, 30), (100, 30), (110, 30), (120, 30),
    (50, 20), (60, 20), (70, 20), (80, 20), (90, 20), (100, 20), (110, 20),
    (60, 10), (70, 10), (80, 10), (90, 10), (100, 10), (110, 10),
    (70, 0), (80, 0), (90, 0), (100, 0), (110, 0),
    (90, -10), (100, -10), (110, -10), (120, -10),
    (90, -20), (100, -20), (110, -20), (120, -20), (130, -20),
    (110, -30), (120, -30), (130, -30), (140, -30), (150, -30),
    (110, -40), (120, -40), (130, -40), (140, -40), (150, -40),
]

PINS = [
    (1, "Santa Clara", -122, 37),
    (2, "London", 0, 51),
    (3, "Orbit", 10, 50),
    (4, "Kyiv", 30, 50),
    (5, "Gaza", 34, 31),
    (6, "Islamabad", 73, 34),
    (7, "Kathmandu", 85, 28),
    (8, "Panama City", -80, 9),
    (9, "Berlin", 13, 52),
    (10, "Murmansk", 33, 69),
    (11, "Bangkok", 100, 14),
    (12, "Madrid", -4, 40),
    (13, "Jakarta", 107, -6),
]

def lonlat_to_xy(lon: float, lat: float, mx: int, my: int, mw: int, mh: int) -> tuple[int, int]:
    x = mx + int((lon + 180) / 360 * mw)
    y = my + int((90 - lat) / 180 * mh)
    return x, y

# ═══ MAIN GENERATION WITH FIXED Y POSITIONS ═══
def generate() -> Image.Image:
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    GAP = 5
    GAP8 = 16  # minimum 8px CLEAR visual gap for Cluster A bands (font metrics need extra)
    MASTHEAD_GAP = 12  # fixed: was 5px, now 12px for clear gap after title

    # ═══ MEASURE ALL FONT METRICS ═══
    title_h = font_height(draw, F_TITLE)
    title_ascent = font_ascent(draw, F_TITLE)
    title_descent = font_descent(draw, F_TITLE)
    subhead_h = font_height(draw, F_SUBHEAD)
    subhead_ascent = font_ascent(draw, F_SUBHEAD)
    subhead_descent = font_descent(draw, F_SUBHEAD)
    headline_h = font_height(draw, F_HEADLINE)
    headline_ascent = font_ascent(draw, F_HEADLINE)
    headline_descent = font_descent(draw, F_HEADLINE)
    subhead2_font = load_font(SERIF, 15)
    subhead2_h = font_height(draw, subhead2_font)
    subhead2_ascent = font_ascent(draw, subhead2_font)
    subhead2_descent = font_descent(draw, subhead2_font)
    one_sky_font = load_font(SANS_BOLD, 11)
    one_sky_h = font_height(draw, one_sky_font)
    one_sky_ascent = font_ascent(draw, one_sky_font)
    one_sky_descent = font_descent(draw, one_sky_font)
    stat_num_h = font_height(draw, F_STAT_NUM)
    stat_num_ascent = font_ascent(draw, F_STAT_NUM)
    stat_num_descent = font_descent(draw, F_STAT_NUM)
    stat_lbl_h = font_height(draw, F_STAT_LBL)
    stat_lbl_ascent = font_ascent(draw, F_STAT_LBL)
    stat_lbl_descent = font_descent(draw, F_STAT_LBL)
    tab_h = font_height(draw, F_TAB) + 5  # chip height (includes padding)
    utc_h = font_height(draw, F_HEADLINE_SM)
    utc_ascent = font_ascent(draw, F_HEADLINE_SM)
    utc_descent = font_descent(draw, F_HEADLINE_SM)
    timeline_h = font_height(draw, F_TIMELINE)
    timeline_ascent = font_ascent(draw, F_TIMELINE)
    timeline_descent = font_descent(draw, F_TIMELINE)
    timeline_evt_h = font_height(draw, F_TIMELINE_EVT)
    panel_sky_h = 130
    panel_h = 140
    day_in_ten_h = utc_h
    day_in_ten_ascent = utc_ascent
    day_in_ten_descent = utc_descent
    card_h = 70
    map_h = 100  # reduced from 150
    date_check_box_h = 40  # reduced from 44
    date_check_label_font = load_font(SANS_BOLD, 13)
    date_check_label_h = font_height(draw, date_check_label_font)
    legend_label_h = font_height(draw, F_CAPTION_BOLD)
    legend_chip_h = font_height(draw, F_CAPTION) + 2
    footer_h = font_height(draw, F_FOOTER)
    footer_ascent = font_ascent(draw, F_FOOTER)
    footer_descent = font_descent(draw, F_FOOTER)

    # ═══ BUILD Y POSITIONS TOP-DOWN WITH MEASURED BOUNDING BOXES ═══
    # Each element: baseline_y, then bottom = baseline_y + descent, next baseline = bottom + GAP + next_ascent

    y = MARGIN  # 12

    # 1. MASTHEAD (baseline at y + ascent)
    Y_MASTHEAD_BASELINE = y + title_ascent
    y = Y_MASTHEAD_BASELINE + title_descent + MASTHEAD_GAP

    # 2. SUBHEAD
    Y_SUBHEAD_BASELINE = y + subhead_ascent
    y = Y_SUBHEAD_BASELINE + subhead_descent + GAP

    # 3. DATE HEADLINE
    Y_DATE_HEADLINE_BASELINE = y + headline_ascent
    y = Y_DATE_HEADLINE_BASELINE + headline_descent + GAP8

    # 4. SUBHEAD2
    Y_SUBHEAD2_BASELINE = y + subhead2_ascent
    y = Y_SUBHEAD2_BASELINE + subhead2_descent + GAP8

    # 5. ONE SKY
    Y_ONE_SKY_BASELINE = y + one_sky_ascent
    y = Y_ONE_SKY_BASELINE + one_sky_descent + GAP8

    # 6. STAT NUMBERS — explicit top-anchored band
    STAT_NUM_TOP = y
    STAT_NUM_HEIGHT = 15  # measured: F_STAT_NUM renders 15px tall
    y = STAT_NUM_TOP + STAT_NUM_HEIGHT + 8  # 8px gap

    # 7. STAT LABELS — explicit band below stat numbers
    STAT_LBL_TOP = y
    STAT_LBL_HEIGHT = 9  # measured: F_STAT_LBL renders 9px tall
    y = STAT_LBL_TOP + STAT_LBL_HEIGHT + 8  # 8px gap

    # 8. REGION TABS — explicit band below labels (top-anchored chips)
    REGION_TAB_TOP = y
    REGION_TAB_HEIGHT = tab_h  # chip height including padding
    y = REGION_TAB_TOP + REGION_TAB_HEIGHT + 8  # 8px gap

    # 9. UTC HEADER — explicit band below tabs
    UTC_HEADER_TOP = y
    UTC_HEADER_HEIGHT = 15  # measured: F_HEADLINE_SM renders 15px tall
    y = UTC_HEADER_TOP + UTC_HEADER_HEIGHT + 8  # 8px gap

    # 10. TIME CHIPS + RULER — below UTC header
    TIME_CHIP_TOP = y
    TIME_CHIP_HEIGHT = 7  # measured: F_TIMELINE renders 7px tall
    y = TIME_CHIP_TOP + TIME_CHIP_HEIGHT + 8  # 8px gap to ruler
    Y_RULER = y
    y += 2 + GAP8  # ruler (2px) + gap
    print(f"DEBUG LAYOUT: Cluster A bands: STAT_NUM={STAT_NUM_TOP}-{STAT_NUM_TOP+STAT_NUM_HEIGHT}, STAT_LBL={STAT_LBL_TOP}-{STAT_LBL_TOP+STAT_LBL_HEIGHT}, REGION_TAB={REGION_TAB_TOP}-{REGION_TAB_TOP+REGION_TAB_HEIGHT}, UTC_HDR={UTC_HEADER_TOP}-{UTC_HEADER_TOP+UTC_HEADER_HEIGHT}, TIME_CHIP={TIME_CHIP_TOP}-{TIME_CHIP_TOP+TIME_CHIP_HEIGHT}, RULER={Y_RULER}")

    # 11. TIMELINE EVENTS (4 events, each ~2 lines) - compressed
    Y_TIMELINE_START = y
    y += 4 * (timeline_evt_h * 2 + 1) + GAP

    # 12. LEAD PANELS
    Y_LEAD_PANELS_TOP = y
    y += 180 + GAP  # panel_h = 180

    # 13. DAY IN TEN HEADER (baseline)
    Y_DAY_IN_TEN_BASELINE = y + day_in_ten_ascent
    y = Y_DAY_IN_TEN_BASELINE + day_in_ten_descent + GAP

    # 14. DAY IN TEN CARDS (2 rows) — 8px gap from header
    y += 3  # extra 3px to make total 8px gap (GAP=5 + 3 = 8)
    Y_DAY_IN_TEN_CARDS_TOP = y
    y += 2 * card_h + 4 + GAP  # reduced gap between rows from 6 to 4

    # 15. MAP SECTION
    Y_MAP_SECTION_TOP = y
    y += map_h + GAP  # reduced from 160

    # 16-18. CLUSTER C: DATE CHECK + TAG LEGEND + FOOTER (build bottom-up to guarantee fit)
    # Footer: baseline at max_footer_baseline, 6px bottom margin
    max_footer_baseline = H - 6 - footer_descent  # 1015
    Y_FOOTER_BASELINE = max_footer_baseline
    footer_text_top = Y_FOOTER_BASELINE - footer_ascent  # 1006

    # TAG LEGEND: ends 8px before footer text top
    tag_legend_h = legend_label_h + 4 + legend_chip_h + 4 + legend_chip_h
    Y_TAG_LEGEND_BOTTOM = footer_text_top - 8  # 998
    Y_TAG_LEGEND_TOP = Y_TAG_LEGEND_BOTTOM - tag_legend_h  # 998 - 51 = 947

    # DATE CHECK: ends 8px before TAG LEGEND top
    Y_DATE_CHECK_BOTTOM = Y_TAG_LEGEND_TOP - 8  # 939
    Y_DATE_CHECK_TOP = Y_DATE_CHECK_BOTTOM - date_check_box_h  # 939 - 40 = 899

    # Verify we have space from MAP section
    if y > Y_DATE_CHECK_TOP:
        # Compress MAP section if needed
        Y_MAP_SECTION_TOP = Y_DATE_CHECK_TOP - map_h - GAP
        y = Y_MAP_SECTION_TOP
    else:
        # Normal flow: MAP ends, then gap to DATE CHECK
        pass

    print(f"DEBUG LAYOUT: Cluster C: DATE_CHECK={Y_DATE_CHECK_TOP}-{Y_DATE_CHECK_BOTTOM}, TAG_LEGEND={Y_TAG_LEGEND_TOP}-{Y_TAG_LEGEND_BOTTOM}, FOOTER_BASELINE={Y_FOOTER_BASELINE}, footer_top={footer_text_top}, final_y={Y_FOOTER_BASELINE + footer_descent + 6}")

    # Verify we fit within page height
    if y > H:
        # Compress by reducing some gaps if needed, but our layout should fit
        pass

    # ═══ 1. MASTHEAD ═══
    draw.text((MARGIN, Y_MASTHEAD_BASELINE), "THE WORLD IN ONE DAY", font=F_TITLE, fill=NAVY)
    draw.text((MARGIN, Y_SUBHEAD_BASELINE), "35 STORIES · 7 REGIONS · EVERY ONE DATED TUESDAY 24 NOVEMBER 2026",
              font=F_SUBHEAD, fill=RED)

    # ═══ 2. DATE HEADLINE + SUBHEAD + ONE SKY ═══
    draw.text((MARGIN, Y_DATE_HEADLINE_BASELINE), "Tuesday 24 November 2026", font=F_HEADLINE, fill=BLACK)
    draw.text((MARGIN, Y_SUBHEAD2_BASELINE), "Nvidia CEO reinstated · Gaza children evacuated to UK · Russia readies nuclear orbiter",
              font=subhead2_font, fill=RED)
    draw.text((MARGIN, Y_ONE_SKY_BASELINE), "ONE DAY, ONE SKY — DAWN IN CALIFORNIA · NOON IN LONDON · NIGHT IN ORBIT",
              font=one_sky_font, fill=NAVY)

    # ═══ 3. STAT STRIP — numbers and labels in SEPARATE bands (explicit top-anchored) ═══
    stats = [
        ("4.0", "Pakistan quake"),
        ("450", "German schools threatened"),
        ("500+", "Lahore AQI"),
        ("€1.4bn", "India pledge to Nepal"),
        ("37 mo", "ex-mayor jailed"),
        ("16 km", "Bangkok protest march"),
    ]
    stat_w = CONTENT_W // 6
    sx = MARGIN
    # Stat numbers — drawn at STAT_NUM_TOP (top-anchored with anchor="lt")
    for num, lbl in stats:
        tw, th = measure_text(draw, num, F_STAT_NUM)
        draw.text((sx + (stat_w - tw) // 2, STAT_NUM_TOP), num, font=F_STAT_NUM, fill=RED, anchor="lt")
        sx += stat_w
    # Stat labels — drawn at STAT_LBL_TOP (top-anchored), separate band below numbers
    sx = MARGIN
    for num, lbl in stats:
        lw, lh = measure_text(draw, lbl, F_STAT_LBL)
        draw.text((sx + (stat_w - lw) // 2, STAT_LBL_TOP), lbl, font=F_STAT_LBL, fill=NAVY, anchor="lt")
        sx += stat_w

    # ═══ 4. REGION TABS — own band (top anchored) ═══
    regions = [
        ("EUROPE", 6), ("MIDDLE EAST", 5), ("ASIA-PACIFIC", 7),
        ("AMERICAS", 6), ("AFRICA", 4), ("OCEANIA", 3), ("WORLD", 4),
    ]
    tab_x = MARGIN
    y_tab = REGION_TAB_TOP
    for name, count in regions:
        label = f"{name} {count}"
        tw, th = measure_text(draw, label, F_TAB)
        w = tw + 12
        h = th + 5
        color = REGION_COLOURS[name]
        draw.rounded_rectangle([tab_x, y_tab, tab_x + w, y_tab + h], radius=3, fill=color)
        draw.text((tab_x + 6, y_tab + 2), label, font=F_TAB, fill=WHITE)
        tab_x += w + 4

    # ═══ 5. THE DAY IN UTC — CLEAN RULER ═══
    draw.text((MARGIN, UTC_HEADER_TOP), "THE DAY IN UTC", font=F_HEADLINE_SM, fill=NAVY, anchor="lt")
    ruler_y = Y_RULER
    draw.line([(MARGIN, ruler_y), (W - MARGIN, ruler_y)], fill=RED, width=2)

    events = [
        ("00:30", "UN chief calls for AI safety framework"),
        ("00:40", "Kushner: Trump backs NATO-style guarantees for Ukraine if conditions met"),
        ("00:46", "Gaza children evacuated to Britain"),
        ("01:40", "Murmansk governor detained in Moscow"),
        ("02:20", "China to ease business visas for Indians"),
    ]
    event_count = len(events)
    spacing = CONTENT_W // (event_count + 1)
    for i, (time_str, evt_text) in enumerate(events):
        ex = MARGIN + (i + 1) * spacing
        draw.line([(ex, ruler_y - 3), (ex, ruler_y + 3)], fill=RED, width=2)
        tw, th = measure_text(draw, time_str, F_TIMELINE)
        time_y = TIME_CHIP_TOP
        draw.text((ex - tw // 2, time_y), time_str, font=F_TIMELINE, fill=NAVY, anchor="lt")
        max_evt_w = spacing - 8
        lines = wrap_text(draw, evt_text, F_TIMELINE_EVT, max_evt_w)
        ly = ruler_y + 15  # 10px clear gap below 2px ruler
        print(f"DEBUG TIMELINE: event {i} ex={ex}, ruler_y={ruler_y}, ly={ly}, lines={lines}")
        for line in lines:
            lw, lh = measure_text(draw, line, F_TIMELINE_EVT)
            draw.text((ex - lw // 2, ly), line, font=F_TIMELINE_EVT, fill=BLACK)
            ly += lh + 1

    # ═══ 6. THREE LEAD PANELS — ONE SKY (CLIPPED SCENES) ═══
    panel_w = (CONTENT_W - 20) // 3
    panel_h = 180  # reduced from 200
    panel_x = MARGIN
    sky_h = panel_h - 50
    y = Y_LEAD_PANELS_TOP

    lead_stories = [
        {
            "kicker": "SANTA CLARA, CALIFORNIA",
            "tag": "REPORTED",
            "headline": "Jensen Huang returns to Nvidia HQ,\nfirst day back",
            "body": "Shares surged 31.5% Monday, adding $952bn.\nHuang tells staff: \"I'll be a better CEO.\"",
            "source": "Reuters · AP · CNN",
            "scene_draw": draw_nvidia_hq,
            "sky_draw": draw_dawn_sky,
        },
        {
            "kicker": "LONDON, UNITED KINGDOM",
            "tag": "REPORTED",
            "headline": "Critically injured Gaza children\nevacuated to Britain",
            "body": "Israeli fire kills Palestinian in Gaza;\nchild dies of lead-poisoning complications.",
            "source": "BBC · Al Jazeera · The Times",
            "scene_draw": draw_london_hospital,
            "sky_draw": draw_noon_sky,
        },
        {
            "kicker": "LOW EARTH ORBIT",
            "tag": "CLAIM",
            "headline": "NATO: space is now a security\nRussia readies nuclear orbiter",
            "body": "German media: Moscow could orbit\nnuclear spacecraft by December.",
            "source": "Investopedia · Reuters",
            "scene_draw": draw_orbit_scene,
            "sky_draw": draw_night_sky,
        },
    ]

    # Draw skies first (full panel width)
    sky_y = y
    for i, story in enumerate(lead_stories):
        px = panel_x + i * (panel_w + 10)
        story["sky_draw"](draw, px, sky_y, panel_w, sky_h)

    # Draw panel frames and content with CLIPPED scenes
    for i, story in enumerate(lead_stories):
        px = panel_x + i * (panel_w + 10)
        py = y
        draw.rectangle([px, py, px + panel_w, py + panel_h], outline=(200, 190, 170), width=1)
        kicker_max_w = panel_w - 16
        kicker = story["kicker"]
        kw, kh = measure_text(draw, kicker, F_CAPTION_BOLD)
        if kw > kicker_max_w:
            kicker = "SANTA CLARA, CA" if "SANTA CLARA" in kicker else kicker
            kw, kh = measure_text(draw, kicker, F_CAPTION_BOLD)
        kx, ky = px + 6, py + 6
        kpad_x, kpad_y = 6, 3
        draw.rounded_rectangle([kx, ky, kx + kw + 2 * kpad_x, ky + kh + 2 * kpad_y],
                               radius=4, fill=(20, 20, 40))
        draw.text((kx + kpad_x, ky + kpad_y), kicker, font=F_CAPTION_BOLD, fill=WHITE)
        # Chip in own y-band BELOW kicker: 6px below kicker bottom, 6px inside left edge
        chip_y = ky + kh + 2 * kpad_y + 6
        draw_chip(draw, px + 8, chip_y, story["tag"], F_CAPTION, TAG_COLOURS[story["tag"]])
        scene_x = px + 8
        scene_y = py + 30
        scene_w = panel_w - 16
        scene_h = panel_h - 80
        scene_img = Image.new("RGBA", (scene_w, scene_h), (0, 0, 0, 0))
        scene_draw = ImageDraw.Draw(scene_img)
        if story["scene_draw"] == draw_orbit_scene:
            layer = story["scene_draw"](scene_draw, 0, 0, scene_w, scene_h)
            if layer:
                bg = Image.new("RGB", (scene_w, scene_h), CREAM)
                bg.paste(layer, mask=layer.split()[3])
                img.paste(bg, (scene_x, scene_y))
        else:
            story["scene_draw"](scene_draw, 0, 0, scene_w, scene_h)
            bg = Image.new("RGB", (scene_w, scene_h), CREAM)
            bg.paste(scene_img, mask=scene_img.split()[3])
            img.paste(bg, (scene_x, scene_y))
        hy = py + panel_h - 55
        # Panel 3 (i==2): disable ellipsis so too-long text fails loudly
        no_ellipsis = (i == 2)
        draw_text_box(draw, px + 8, hy, story["headline"], F_HEADLINE_XS, BLACK, panel_w - 16, line_spacing=1, max_lines=2, no_ellipsis=no_ellipsis)
        by = hy + 44
        draw_text_box(draw, px + 8, by, story["body"], F_BODY_SM, DARK_GRAY, panel_w - 16, line_spacing=1, max_lines=2)
        sy = by + 24
        draw.text((px + 8, sy), story["source"], font=F_BODY_XS, fill=MED_GRAY)

    # ═══ 7. THE DAY IN TEN ═══
    draw.text((MARGIN, Y_DAY_IN_TEN_BASELINE), "THE DAY IN TEN", font=F_HEADLINE_SM, fill=NAVY)

    ten_stories = [
        (4, "ARMENIA", "TRIPP project kickoff; draft constitution for Azerbaijan peace", "REPORTED"),
        (5, "UN", "Secretary-General demands AI safety framework within a year", "REPORTED"),
        (6, "POLAND", "Crashed objects classified as Soviet missiles", "OFFICIALS SAY"),
        (7, "PAKISTAN", "4.0 quake near Afghan border; Lahore AQI 500+, 8 cities among worst", "REPORTED"),
        (8, "NEPAL", "India pledges €1.4bn for glacier flood rebuild", "OFFICIALS SAY"),
        (9, "PANAMA", "Govt & First Quantum resume Cobre Panama mine talks", "REPORTED"),
        (10, "GERMANY", "~450 schools receive bomb threats by email", "REPORTED"),
        (11, "RUSSIA", "Murmansk governor Chibis detained in Moscow on misappropriation", "REPORTED"),
        (12, "CULTURE", "Ex-Mossad chief Barnea reveals Taylor Swift Vienna terror plot foiled", "REPORTED"),
        (13, "CHINA", "Beijing ready to facilitate business visas for Indians", "OFFICIALS SAY"),
    ]

    card_w = (CONTENT_W - 32) // 5
    card_h = 92
    y = Y_DAY_IN_TEN_CARDS_TOP
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            num, region, headline, tag = ten_stories[idx]
            cx = MARGIN + col * (card_w + 8)
            cy = y + row * (card_h + 6)
            draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=(250, 247, 235), outline=(200, 190, 170), width=1)
            draw.ellipse([cx + 6, cy + 6, cx + 22, cy + 22], fill=RED)
            nw, nh = measure_text(draw, str(num), F_CAPTION_BOLD)
            draw.text((cx + 14 - nw // 2, cy + 14 - nh // 2), str(num), font=F_CAPTION_BOLD, fill=WHITE)
            rcolor = REGION_COLOURS.get(region, NAVY)
            draw_chip(draw, cx + 26, cy + 7, region, F_BODY_XS, rcolor, pad_x=3, pad_y=1)
            draw_chip(draw, cx + 6, cy + 28, tag, F_BODY_XS, TAG_COLOURS[tag], pad_x=3, pad_y=1)
            draw_mini_illustration(draw, cx + card_w - 28, cy + 28, 24, 24, num)
            draw_text_box(draw, cx + 6, cy + 46, headline, F_BODY_SM, BLACK, card_w - 12, line_spacing=1, max_lines=2)
            draw.text((cx + 6, cy + card_h - 13), "Reuters · AP · BBC", font=F_BODY_XS, fill=MED_GRAY)

    # ═══ 8. WHERE IT HAPPENED + 22 MORE ═══
    map_w = 500
    map_h = 150  # reduced from 160
    map_x = MARGIN
    map_y = Y_MAP_SECTION_TOP
    list_x = map_x + map_w + 14
    list_w = W - list_x - MARGIN

    # Compute header position: below grid with 8px clear gap
    # Grid bottom (actual drawing): Y_DAY_IN_TEN_CARDS_TOP + 2*card_h + 6 (row gap = 6)
    grid_bottom = Y_DAY_IN_TEN_CARDS_TOP + 2 * card_h + 6
    header_text_top = grid_bottom + 8
    draw.text((map_x, header_text_top), "WHERE IT HAPPENED", font=F_HEADLINE_SM, fill=NAVY, anchor="lt")
    # Map content starts 8px below header bottom (header height ~15px with anchor="lt")
    map_content_y = header_text_top + 15 + 8
    # Shrink map height to fit before DATE CHECK with 8px gap
    available_map_h = max(20, Y_DATE_CHECK_TOP - 8 - map_content_y)
    map_h = available_map_h + 22  # +22 for header space in map_h variable used by lonlat_to_xy

    # Hard vertical divider at x=514 (list starts at 526, 12px clear)
    MAP_CLIP_X = 514
    # Pin radius is 6, land dot radius is 1. Clip centers so edges don't cross 514.
    PIN_CLIP_X = MAP_CLIP_X - 6   # 508
    DOT_CLIP_X = MAP_CLIP_X - 1   # 513

    for lon, lat in LAND_GRID:
        dx, dy = lonlat_to_xy(lon, lat, map_x, map_content_y, map_w, available_map_h)
        if map_x <= dx <= DOT_CLIP_X and map_content_y <= dy < map_content_y + available_map_h:
            draw.ellipse([dx - 1, dy - 1, dx + 1, dy + 1], fill=(160, 150, 130))

    for num, name, lon, lat in PINS:
        px, py = lonlat_to_xy(lon, lat, map_x, map_content_y, map_w, available_map_h)
        if map_x <= px <= PIN_CLIP_X and map_content_y <= py < map_content_y + available_map_h:
            draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED, outline=WHITE, width=1)
            nw, nh = measure_text(draw, str(num), F_MAP_NUM)
            draw.text((px - nw // 2, py - nh // 2), str(num), font=F_MAP_NUM, fill=WHITE)

    # 22 MORE list — FIXED: hard column boundaries with 32px gap, ONE LINE PER ITEM with ellipsis
    list_y = map_y + 22
    also_on_header = "ALSO ON TUE 24 NOV — 22 MORE"
    draw.text((list_x, list_y), also_on_header, font=F_HEADLINE_SM, fill=NAVY)
    list_y += 22

    also_on = [
        "14 Latvia PM refuses to restore ties with Russia — Reuters",
        "15 Russia warns Estonia its moves risk open war — AP",
        "16 Iraqi leader arrives in Egypt on first official visit — BBC",
        "17 Trump targets Newsom in DOJ speech over 548 commutations — CNN",
        "18 Ex-Mississippi mayor jailed 37 months for bribery — AP",
        "19 Spain's Supreme Court amnesties Carles Puigdemont — El País",
        "20 Dutch activist Jason Bhugwandass dies by euthanasia at 28 — NOS",
        "21 Indonesia factory fire kills 26, dozens missing in Banten — Kompas",
        "22 Bangladesh garment workers reject pay offer; Yunus says Grameen targeted — Bdnews24",
        "23 Syria–EU envoys fear focus on return of displaced persons — Al Jazeera",
        "24 Myanmar urged to follow intl law after ICJ ruling on Rohingya — Reuters",
        "25 UN warns Libya must not become Russia–Ukraine battleground — AP",
        "26 Belarus opposition figure calls for talks with Lukashenko — BBC",
        "27 Kim says the North seeks protection, not control — KCNA",
        "28 Lavrov voices concern over Lebanon, calls for Syrian unity — TASS",
        "29 Vietnam to address trade surplus amid US pressure — VnExpress",
        "30 Taliban deploy officers to defend disappearing woodlands — TOLO",
        "31 US seeks answers on Nvidia chip sales to China, Bessent says — Bloomberg",
        "32 Russia plans $576m railway ferries for Kaliningrad — Izvestia",
        "33 Pauline Hanson faces biggest trial as QLD vote looms — ABC",
        "34 Thai protesters march 16 km to Bangchak refinery; court bails MP — Bangkok Post",
        "35 Anthropic shares fall as AI trade roars back on Huang's return — The Information",
    ]

    # Two columns with 48px gap at midpoint — left column never crosses midpoint, right never crosses right edge
    col_gap = 48
    col_w = (list_w - col_gap) // 2
    left_col_x = list_x
    right_col_x = list_x + col_w + col_gap
    line_h = 13  # font size 9 + 4px gap
    print(f"DEBUG LIST: list_x={list_x}, list_w={list_w}, col_w={col_w}, left_col_x={left_col_x}, right_col_x={right_col_x}")
    for i, line in enumerate(also_on):
        col = i // 11
        row = i % 11
        lx = left_col_x if col == 0 else right_col_x
        ly = list_y + row * line_h
        # HARD clipping to column width — render on temp surface and paste clipped
        draw_text_clipped(draw, img, lx, ly, line, F_BODY_XS, BLACK, col_w - 4, max_lines=1)

    # ═══ 9. DATE CHECK — shortened to fit in box ═══
    box_x = MARGIN
    box_y = Y_DATE_CHECK_TOP
    box_w = CONTENT_W
    box_h = date_check_box_h

    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=5, fill=(220, 40, 30))
    draw.text((box_x + 10, box_y + 5), "DATE CHECK", font=date_check_label_font, fill=WHITE)

    # SHORTENED to fit in 2 lines inside box (max_w = box_w - 20 = 984)
    check_text = (
        "Wires read to 02:20 UTC. Every story here happened or was first reported Tue 24 Nov 2026 in some zone. "
        "Omitted: COP31 collapse (Sun 22 Nov) · Russia 400-drone barrage (19–20 Nov) · Ukraine sinks corvette (Sun 22 Nov) · "
        "Nvidia reinstates Huang (Mon 23 Nov) · Manchester evacuation (Sun 22 Nov) · SK minister quits (Sun 22 Nov) · "
        "China death sentence (Mon 23 Nov) · Kyiv strike (Mon 23 Nov) · Houthi Taiz attacks (Mon 23 Nov) · IRGC claims (7–20 Nov)."
    )
    draw_text_box(draw, box_x + 10, box_y + 20, check_text, F_BODY_XS, WHITE, box_w - 20, line_spacing=1, max_lines=2)

    # ═══ 10. TAG LEGEND — own row below DATE CHECK box ═══
    legend_y = Y_TAG_LEGEND_TOP
    draw.text((box_x, legend_y), "TAG LEGEND", font=F_CAPTION_BOLD, fill=NAVY)
    legend_y += legend_label_h + 4  # 4px gap to chips row
    tags = [
        ("ONGOING", "still developing"),
        ("REPORTED", "one source's claim, not yet confirmed"),
        ("CLAIM", "a party's claim, contested"),
        ("OFFICIALS SAY", "attributed, not verified"),
    ]
    # Row 1: chips only
    lx = box_x
    for tag, _ in tags:
        cw, ch = draw_chip(draw, lx, legend_y, tag, F_CAPTION, TAG_COLOURS[tag], pad_x=4, pad_y=1)
        lx += cw + 8
    # Row 2: descriptions (wrapped to fit width)
    legend_y += legend_chip_h + 4  # 4px gap to descriptions row
    lx = box_x
    for _, desc in tags:
        draw.text((lx, legend_y), desc, font=F_LEGEND, fill=DARK_GRAY)
        lw, _ = measure_text(draw, desc, F_LEGEND)
        lx += lw + 18
    # If total width exceeds, wrap to third line (but should fit in 2 rows)

    # ═══ 11. FOOTER — centered, fully inside page with 6px bottom margin ═══
    footer = "Sources: Reuters · AP · CNN · BBC · Al Jazeera · The Times · Investopedia"
    fw, fh = measure_text(draw, footer, F_FOOTER)
    draw.text((W // 2 - fw // 2, Y_FOOTER_BASELINE), footer, font=F_FOOTER, fill=DARK_GRAY, anchor="ls")

    return img

# ─── Self-check ─────────────────────────────────────────────────────────────
def self_check(img: Image.Image) -> tuple[bool, list[str]]:
    errors = []
    if img.size != (1024, 1024):
        errors.append(f"Wrong size: {img.size}")
    if img.mode != "RGB":
        errors.append(f"Wrong mode: {img.mode}")
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    size = buf.tell()
    if size > 1048576:
        errors.append(f"File too large: {size} bytes (> 1 MiB)")
    # Check footer is visible (baseline at ~1014, text renders ~1004-1024)
    footer_y = 1014
    footer_ok = False
    for cx in range(W//2 - 10, W//2 + 11):
        p = img.getpixel((cx, footer_y))
        if p != CREAM:
            footer_ok = True
            break
    if not footer_ok:
        errors.append("Footer area is cream (may be missing)")
    # Check orbit arc doesn't escape panel 3 (sample pixels below panel 3)
    # Panel 3: x ~ 680-1012, y ~ 310-510. Check below panel 3 for dark blue pixels
    escape_check = img.getpixel((800, 555))
    if escape_check == (0, 0, 0) or (escape_check[0] < 50 and escape_check[1] < 80 and escape_check[2] > 120):
        errors.append("Orbit arc may escape panel 3 (dark blue pixels found below)")
    return len(errors) == 0, errors

def main():
    out_dir = Path("/workspace/news-image-20261124/out")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "entry.png"

    print("Generating entry.png...")
    img = generate()
    img.save(out_path, "PNG", optimize=True)
    print(f"Saved to {out_path}")

    ok, errors = self_check(img)
    if ok:
        print("Self-check: PASSED")
    else:
        print("Self-check: FAILED")
        for e in errors:
            print(f"  - {e}")

    size = out_path.stat().st_size
    print(f"File size: {size} bytes ({size/1024:.1f} KiB)")

    import hashlib
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"SHA256: {sha}")

if __name__ == "__main__":
    main()