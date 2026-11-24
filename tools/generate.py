#!/usr/bin/env python3
"""
News Image Generator for make.fun news-image-20261124
Generates a 1024x1024 newspaper front page for Tuesday 24 November 2026
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# ─── Constants ───
W, H = 1024, 1024
CREAM = (250, 246, 235)
BLACK = (25, 25, 25)
NAVY = (20, 35, 65)
RED = (195, 35, 35)
DARK_RED = (140, 25, 25)
GREY = (90, 90, 90)
LIGHT_GREY = (180, 180, 180)
WHITE = (255, 255, 255)

# Region colors
REGION_COLORS = {
    "EUROPE": (0, 90, 160),
    "MIDDLE EAST": (180, 110, 0),
    "ASIA-PACIFIC": (0, 120, 60),
    "AMERICAS": (160, 30, 60),
    "AFRICA": (200, 150, 0),
    "OCEANIA": (100, 60, 160),
    "WORLD": (80, 80, 80),
}

# Tag colors
TAG_COLORS = {
    "ONGOING": (200, 140, 0),
    "REPORTED": (0, 100, 160),
    "CLAIM": (180, 40, 40),
    "OFFICIALS SAY": (120, 60, 140),
}

FONT_DIR = "/workspace/news-image-20261124/fonts/dejavu-fonts-ttf-2.37/ttf"

# ─── Font loading ───
def load_font(name, size):
    path = os.path.join(FONT_DIR, name)
    return ImageFont.truetype(path, size)

F_SERIF_BOLD_48 = load_font("DejaVuSerif-Bold.ttf", 48)
F_SERIF_BOLD_44 = load_font("DejaVuSerif-Bold.ttf", 44)
F_SERIF_BOLD_36 = load_font("DejaVuSerif-Bold.ttf", 36)
F_SERIF_BOLD_28 = load_font("DejaVuSerif-Bold.ttf", 28)
F_SERIF_BOLD_26 = load_font("DejaVuSerif-Bold.ttf", 26)
F_SERIF_BOLD_24 = load_font("DejaVuSerif-Bold.ttf", 24)
F_SERIF_BOLD_20 = load_font("DejaVuSerif-Bold.ttf", 20)
F_SERIF_BOLD_18 = load_font("DejaVuSerif-Bold.ttf", 18)
F_SERIF_BOLD_16 = load_font("DejaVuSerif-Bold.ttf", 16)
F_SERIF_BOLD_14 = load_font("DejaVuSerif-Bold.ttf", 14)
F_SERIF_BOLD_13 = load_font("DejaVuSerif-Bold.ttf", 13)
F_SERIF_BOLD_12 = load_font("DejaVuSerif-Bold.ttf", 12)
F_SERIF_ITALIC_18 = load_font("DejaVuSerif-Italic.ttf", 18)
F_SERIF_ITALIC_16 = load_font("DejaVuSerif-Italic.ttf", 16)
F_SERIF_ITALIC_14 = load_font("DejaVuSerif-Italic.ttf", 14)
F_SERIF_ITALIC_12 = load_font("DejaVuSerif-Italic.ttf", 12)
F_SANS_BOLD_20 = load_font("DejaVuSans-Bold.ttf", 20)
F_SANS_BOLD_16 = load_font("DejaVuSans-Bold.ttf", 16)
F_SANS_BOLD_14 = load_font("DejaVuSans-Bold.ttf", 14)
F_SANS_BOLD_12 = load_font("DejaVuSans-Bold.ttf", 12)
F_SANS_BOLD_11 = load_font("DejaVuSans-Bold.ttf", 11)
F_SANS_BOLD_10 = load_font("DejaVuSans-Bold.ttf", 10)
F_SANS_BOLD_9 = load_font("DejaVuSans-Bold.ttf", 9)
F_SANS_BOLD_8 = load_font("DejaVuSans-Bold.ttf", 8)
F_SANS_BOLD_7 = load_font("DejaVuSans-Bold.ttf", 7)
F_SANS_BOLD_6 = load_font("DejaVuSans-Bold.ttf", 6)
F_SANS_14 = load_font("DejaVuSans.ttf", 14)
F_SANS_12 = load_font("DejaVuSans.ttf", 12)
F_SANS_11 = load_font("DejaVuSans.ttf", 11)
F_SANS_10 = load_font("DejaVuSans.ttf", 10)
F_SANS_9 = load_font("DejaVuSans.ttf", 9)
F_SANS_8 = load_font("DejaVuSans.ttf", 8)
F_SANS_7 = load_font("DejaVuSans.ttf", 7)
F_SANS_6 = load_font("DejaVuSans.ttf", 6)
F_MONO_BOLD_12 = load_font("DejaVuSansMono-Bold.ttf", 12)

# ─── Helpers ───
def draw_text(draw, xy, text, font, fill=BLACK, anchor="la"):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)

def measure_text(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width, return list of lines."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        w, _ = measure_text(draw, test, font)
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

def draw_wrapped(draw, xy, text, font, fill=BLACK, max_width=None, line_spacing=1.2, anchor="la"):
    """Draw wrapped text, return (width_used, height_used)."""
    if max_width is None:
        draw_text(draw, xy, text, font, fill, anchor)
        w, h = measure_text(draw, text, font)
        return w, h
    lines = wrap_text(draw, text, font, max_width)
    x, y = xy
    total_h = 0
    max_w = 0
    for line in lines:
        draw_text(draw, (x, y), line, font, fill, anchor)
        w, h = measure_text(draw, line, font)
        max_w = max(max_w, w)
        total_h += int(h * line_spacing)
        y += int(h * line_spacing)
    return max_w, total_h

def draw_rect(draw, xy, size, fill, outline=None, width=1):
    x, y = xy
    w, h = size
    draw.rectangle([x, y, x+w, y+h], fill=fill, outline=outline, width=width)

def draw_rounded_rect(draw, xy, size, radius, fill, outline=None, width=1):
    x, y = xy
    w, h = size
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=width)

# ─── Illustration primitives ───
def draw_satellite(draw, cx, cy, size=8, color=NAVY):
    """Draw a simple satellite."""
    # Main body
    draw.rectangle([cx-size//2, cy-size//2, cx+size//2, cy+size//2], fill=color)
    # Solar panels
    draw.rectangle([cx-size*2, cy-2, cx-size//2, cy+2], fill=(100,100,100))
    draw.rectangle([cx+size//2, cy-2, cx+size*2, cy+2], fill=(100,100,100))

def draw_nvidia_hq_scene(draw, x, y, w, h):
    """Draw Nvidia HQ at dawn - California."""
    # Sky gradient dawn
    for i in range(h):
        ratio = i / h
        r = int(255 * (1 - ratio * 0.6))
        g = int(200 * (1 - ratio * 0.5))
        b = int(150 * (1 - ratio * 0.3))
        draw.line([(x, y+i), (x+w, y+i)], fill=(r, g, b))
    # Building silhouette
    bh = int(h * 0.6)
    draw.rectangle([x+w//4, y+h-bh, x+3*w//4, y+h], fill=(40, 30, 50))
    # Windows glint
    for wx in range(x+w//4+10, x+3*w//4-10, 20):
        for wy in range(y+h-bh+10, y+h-10, 18):
            if (wx + wy) % 40 < 20:
                draw.rectangle([wx, wy, wx+8, wy+6], fill=(255, 220, 100))
    # "NVIDIA" sign
    draw_text(draw, (x+w//2, y+h-bh-20), "NVIDIA HQ", F_SANS_BOLD_14, fill=(255,220,100), anchor="mm")

def draw_london_hospital_scene(draw, x, y, w, h):
    """Draw London hospital scene - Gaza children arriving (redesigned)."""
    # Sky - pale morning blue
    draw.rectangle([x, y, x+w, y+h], fill=(160, 190, 220))
    # Ground
    draw.rectangle([x, y+int(h*0.68), x+w, y+h], fill=(70, 110, 50))
    # Hospital building - white with red cross
    hosp_w = int(w * 0.65)
    hosp_h = int(h * 0.55)
    hosp_x = x + (w - hosp_w) // 2
    hosp_y = y + h - hosp_h - int(h * 0.08)
    draw.rectangle([hosp_x, hosp_y, hosp_x + hosp_w, hosp_y + hosp_h], fill=(240, 240, 240), outline=(200, 200, 200), width=1)
    # Hospital windows
    for wx in range(hosp_x + 10, hosp_x + hosp_w - 10, 18):
        for wy in range(hosp_y + 10, hosp_y + hosp_h - 10, 16):
            draw.rectangle([wx, wy, wx+10, wy+8], fill=(180, 210, 240))
    # Red cross on hospital
    cross_x = hosp_x + hosp_w // 2
    cross_y = hosp_y + 15
    draw.rectangle([cross_x - 12, cross_y - 3, cross_x + 12, cross_y + 3], fill=RED)
    draw.rectangle([cross_x - 3, cross_y - 12, cross_x + 3, cross_y + 12], fill=RED)
    # Ambulance - white with red stripe and blue lights
    amb_x = x + 15
    amb_y = y + h - 55
    draw.rectangle([amb_x, amb_y, amb_x + 60, amb_y + 25], fill=WHITE, outline=(200,200,200), width=1)
    draw.rectangle([amb_x + 5, amb_y + 3, amb_x + 55, amb_y + 22], fill=RED)
    # Blue lights on ambulance
    draw.ellipse([amb_x + 8, amb_y + 5, amb_x + 14, amb_y + 11], fill=(0, 80, 200))
    draw.ellipse([amb_x + 46, amb_y + 5, amb_x + 52, amb_y + 11], fill=(0, 80, 200))
    # Small figures (children with medical staff)
    for i, fx in enumerate([hosp_x + hosp_w + 10, hosp_x + hosp_w + 28, hosp_x + hosp_w + 46]):
        # Head
        draw.ellipse([fx, amb_y - 8, fx + 10, amb_y + 2], fill=(255, 220, 180))
        # Body - blue for staff, lighter for children
        body_color = (60, 120, 180) if i == 0 else (100, 160, 220)
        draw.rectangle([fx + 1, amb_y + 2, fx + 9, amb_y + 18], fill=body_color)
    # Union Jack hint - small flag on hospital roof
    flag_x = hosp_x + hosp_w - 25
    flag_y = hosp_y - 18
    draw.rectangle([flag_x, flag_y, flag_x + 20, flag_y + 12], fill=WHITE, outline=(180,180,180))
    # Union Jack pattern (simplified)
    draw.rectangle([flag_x, flag_y, flag_x + 20, flag_y + 12], fill=(0, 36, 125))
    draw.rectangle([flag_x + 6, flag_y, flag_x + 14, flag_y + 12], fill=WHITE)
    draw.rectangle([flag_x, flag_y + 3, flag_x + 20, flag_y + 9], fill=WHITE)
    draw.rectangle([flag_x + 6, flag_y + 6, flag_x + 14, flag_y + 6], fill=RED)
    draw.rectangle([flag_x + 9, flag_y, flag_x + 11, flag_y + 12], fill=RED)
    # Big Ben silhouette in far background
    bb_x = x + w - 50
    bb_y = y + h - 140
    draw.rectangle([bb_x, bb_y, bb_x + 30, y + h - 10], fill=(50, 50, 70))
    draw.ellipse([bb_x + 2, bb_y - 20, bb_x + 28, bb_y + 8], fill=(70, 70, 90))

def draw_orbit_scene(draw, x, y, w, h):
    """Draw orbit above Europe - nuclear orbiter."""
    # Space background
    draw.rectangle([x, y, x+w, y+h], fill=(10, 10, 30))
    # Stars
    import random
    random.seed(42)
    for _ in range(50):
        sx = x + random.randint(0, w)
        sy = y + random.randint(0, h)
        draw.ellipse([sx, sy, sx+1, sy+1], fill=WHITE)
    # Earth curve at bottom - CLIPPED to panel bounds
    earth_r = w * 2
    earth_cy = y + h + earth_r // 2
    # Only draw the visible portion within panel: clip to panel rectangle
    # Draw a filled chord/segment instead of full ellipse
    # The visible part is the top edge of the earth curve at the panel bottom
    clip_box = [x, y, x+w, y+h]
    # Draw earth curve as a filled rectangle with rounded top (simulating earth limb)
    limb_h = 30
    draw.rectangle([x, y+h-limb_h, x+w, y+h], fill=(0, 60, 120))
    # Rounded top edge for earth limb
    draw.ellipse([x-2, y+h-limb_h-10, x+w+2, y+h+10], fill=(0, 60, 120))
    # Earth atmosphere glow - thin line along top of limb
    draw.arc([x-5, y+h-limb_h-15, x+w+5, y+h+5], 0, 180, fill=(0, 120, 200), width=2)
    # Satellite/orbiter
    sat_x = x + w//2
    sat_y = y + h//3
    draw_satellite(draw, sat_x, sat_y, 10, RED)
    # Orbital path (thin line)
    draw.arc([sat_x - 80, sat_y - 80, sat_x + 80, sat_y + 80], 0, 360, fill=(100, 100, 150), width=1)
    # "NUCLEAR ORBITER" label
    draw_text(draw, (sat_x, sat_y + 50), "NUCLEAR ORBITER", F_SANS_BOLD_10, fill=RED, anchor="mm")

# ─── Mini illustrations for THE DAY IN TEN ───
def draw_mini_icon(draw, cx, cy, icon_type, color):
    """Draw a simple flat colored icon at (cx, cy) within ~16x16 area."""
    s = 8  # half-size
    if icon_type == "flag":  # Armenia peace
        draw.rectangle([cx-s, cy-s, cx+s, cy+s], fill=color)
        draw.rectangle([cx-s, cy, cx+s, cy+s], fill=(255,255,255))
    elif icon_type == "building":  # UN
        draw.rectangle([cx-s, cy, cx+s, cy+s], fill=color)
        draw.rectangle([cx-4, cy-s, cx+4, cy], fill=color)
        draw.rectangle([cx-2, cy-s-4, cx+2, cy-s], fill=WHITE)
    elif icon_type == "missile":  # Poland missiles
        draw.rectangle([cx-2, cy-s, cx+2, cy+s], fill=color)
        draw.polygon([(cx, cy-s-4), (cx-3, cy-s), (cx+3, cy-s)], fill=color)
    elif icon_type == "wave":  # Pakistan quake/AQI
        draw.arc([cx-s*2, cy-s, cx+s*2, cy+s*2], 0, 180, fill=color, width=2)
        draw.arc([cx-s*1.5, cy-s+2, cx+s*1.5, cy+s], 0, 180, fill=color, width=1)
    elif icon_type == "mountain":  # Nepal glacier
        draw.polygon([(cx, cy-s-4), (cx-s*2, cy+s), (cx+s*2, cy+s)], fill=color)
        draw.polygon([(cx, cy-s), (cx-s, cy), (cx+s, cy)], fill=WHITE)
    elif icon_type == "mine":  # Panama mine
        draw.rectangle([cx-s, cy, cx+s, cy+s], fill=color)
        draw.line([cx, cy, cx, cy+s*2], fill=color, width=2)
        draw.line([cx-s, cy+s, cx+s, cy+s], fill=color, width=2)
    elif icon_type == "warning":  # Germany bomb threats
        draw.polygon([(cx, cy-s-2), (cx-s*1.5, cy+s), (cx+s*1.5, cy+s)], fill=color)
        draw.rectangle([cx-1, cy-s+2, cx+1, cy], fill=WHITE)
        draw.ellipse([cx-1, cy+2, cx+1, cy+4], fill=WHITE)
    elif icon_type == "gavel":  # Russia governor detained
        draw.rectangle([cx-s, cy-s, cx+s, cy-s+4], fill=color)
        draw.rectangle([cx-1, cy-s+4, cx+1, cy+s], fill=(100,100,100))
    elif icon_type == "star":  # Taylor Swift/ISIS plot
        # Simple 5-point star
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            r_outer = s * 1.5 if i % 2 == 0 else s * 0.6
            points.append((cx + r_outer * math.cos(angle), cy + r_outer * math.sin(angle)))
        draw.polygon(points, fill=color)
    elif icon_type == "plane":  # China visas
        draw.line([cx-s*2, cy, cx+s*2, cy], fill=color, width=2)
        draw.line([cx, cy-s, cx, cy+s], fill=color, width=2)
        draw.line([cx-s, cy-s, cx+s, cy+s], fill=color, width=1)
        draw.line([cx-s, cy+s, cx+s, cy-s], fill=color, width=1)
    elif icon_type == "pill":  # Health/medical
        draw.rounded_rectangle([cx-s*1.5, cy-4, cx+s*1.5, cy+4], radius=4, fill=color)
        draw.line([cx, cy-2, cx, cy+2], fill=WHITE, width=2)
    else:  # default flag
        draw.rectangle([cx-s, cy-s, cx+s, cy+s], fill=color)

# ─── Main generation ───
def generate():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    y = 0
    margin = 24
    content_w = W - 2 * margin

    # ═══════════════════════════════════════
    # 1. MASTHEAD
    # ═══════════════════════════════════════
    masthead_h = 56
    draw_rect(draw, (0, y), (W, masthead_h), NAVY)
    draw_text(draw, (W//2, y + 16), "THE WORLD IN ONE DAY", F_SERIF_BOLD_36, fill=WHITE, anchor="mm")
    draw_text(draw, (W//2, y + 46), "35 STORIES · 7 REGIONS · EVERY ONE DATED TUESDAY 24 NOVEMBER 2026", F_SANS_BOLD_11, fill=(200,200,220), anchor="mm")
    y += masthead_h + 4

    # ═══════════════════════════════════════
    # 2. MAIN HEADLINE + SUBHEAD
    # ═══════════════════════════════════════
    draw_text(draw, (margin, y), "Tuesday 24 November 2026", F_SERIF_BOLD_44, fill=BLACK, anchor="la")
    y += 48
    subhead = "Nvidia's Huang returns · Gaza children evacuated to UK · Russia readies nuclear orbiter"
    draw_text(draw, (margin, y), subhead, F_SERIF_ITALIC_18, fill=RED, anchor="la")
    y += 26
    # Red rule
    draw.line([(margin, y), (W - margin, y)], fill=RED, width=2)
    y += 8

    # ═══════════════════════════════════════
    # 3. STAT STRIP (6 big red numbers)
    # ═══════════════════════════════════════
    stat_h = 42
    stats = [
        ("4.0", "Pakistan quake"),
        ("450", "German schools threatened"),
        ("500+", "Lahore AQI"),
        ("€1.4bn", "India pledge to Nepal"),
        ("37 mo", "Ex-mayor jailed"),
        ("16 km", "Bangkok protest march"),
    ]
    stat_w = content_w // 6
    for i, (num, label) in enumerate(stats):
        sx = margin + i * stat_w
        draw_text(draw, (sx + stat_w//2, y + 8), num, F_SERIF_BOLD_26, fill=RED, anchor="mm")
        draw_text(draw, (sx + stat_w//2, y + 32), label, F_SANS_8, fill=GREY, anchor="mm")
    y += stat_h + 4

    # ═══════════════════════════════════════
    # 4. REGION TABS
    # ═══════════════════════════════════════
    tab_h = 28
    regions = [
        ("EUROPE", "6"),
        ("MIDDLE EAST", "5"),
        ("ASIA-PACIFIC", "7"),
        ("AMERICAS", "6"),
        ("AFRICA", "4"),
        ("OCEANIA", "3"),
        ("WORLD", "4"),
    ]
    tab_w = content_w // 7
    for i, (name, count) in enumerate(regions):
        tx = margin + i * tab_w
        color = REGION_COLORS[name]
        draw_rounded_rect(draw, (tx, y), (tab_w - 2, tab_h), 4, fill=color)
        draw_text(draw, (tx + tab_w//2, y + 7), name, F_SANS_BOLD_9, fill=WHITE, anchor="mm")
        draw_text(draw, (tx + tab_w//2, y + 19), count, F_SANS_BOLD_11, fill=WHITE, anchor="mm")
    y += tab_h + 6

    # ═══════════════════════════════════════
    # 5. THE DAY IN UTC TIMELINE (rebuilt)
    # ═══════════════════════════════════════
    draw_text(draw, (margin, y), "THE DAY IN UTC", F_SERIF_BOLD_16, fill=NAVY, anchor="la")
    y += 22
    timeline_h = 70  # taller to accommodate wrapped text
    timeline_events = [
        ("00:30", "UN chief calls for AI safety framework"),
        ("00:40", "Kushner: Trump would back NATO-style guarantees for Ukraine"),
        ("00:46", "Gaza children evacuated to Britain"),
        ("01:40", "Murmansk governor detained in Moscow"),
        ("02:20", "China to ease business visas for Indians"),
    ]
    tl_w = content_w // 5
    for i, (time, event) in enumerate(timeline_events):
        tx = margin + i * tl_w
        col_center = tx + tl_w // 2
        # Time chip ON TOP - navy circle with white time
        chip_y = y + 14
        draw.ellipse([col_center-14, chip_y-14, col_center+14, chip_y+14], fill=NAVY)
        draw_text(draw, (col_center, chip_y), time, F_MONO_BOLD_12, fill=WHITE, anchor="mm")
        # Event text WRAPPED below chip, centered in column
        text_x = tx + 4
        text_w = tl_w - 8
        draw_wrapped(draw, (text_x, chip_y + 18), event, F_SANS_8, fill=BLACK, max_width=text_w, line_spacing=1.15, anchor="la")
    y += timeline_h + 6

    # ═══════════════════════════════════════
    # 6. THREE LEAD PANELS (with THIN satellite arc ONLY across top)
    # ═══════════════════════════════════════
    lead_h = 230
    panel_w = content_w // 3
    panel_gap = 4

    # Draw THIN satellite arc ONLY across the top illustration area (y+20 to y+135)
    # Arc center below the illustration band, radius so arc stays within illustration y-range
    arc_center_x = margin + panel_w * 1.5
    arc_center_y = y + 220  # below illustration band (which ends at y+135)
    arc_radius = 200  # reaches left/right panel edges, arc stays within y+20..y+120
    # Draw thin stroked arc from 210° to 330° (shallow curve across top of panels)
    draw.arc(
        [arc_center_x - arc_radius, arc_center_y - arc_radius,
         arc_center_x + arc_radius, arc_center_y + arc_radius],
        210, 330, fill=NAVY, width=2
    )
    # Three tiny satellite dots ON the arc line
    for angle in [230, 270, 310]:
        rad = math.radians(angle)
        sat_x = arc_center_x + int(arc_radius * math.cos(rad))
        sat_y = arc_center_y + int(arc_radius * math.sin(rad))
        draw_satellite(draw, sat_x, sat_y, 5, NAVY)
    # "ONE DAY, ONE ORBIT" label - small, above arc
    draw_text(draw, (W//2, y + 10), "ONE DAY, ONE ORBIT", F_SANS_BOLD_9, fill=NAVY, anchor="mm")

    # Panel 1: NVIDIA
    px1 = margin
    draw_nvidia_hq_scene(draw, px1, y + 20, panel_w - panel_gap, 115)
    py1 = y + 145
    # Kicker tags
    draw_rounded_rect(draw, (px1 + 4, py1), (75, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px1 + 41, py1 + 8), "SANTA CLARA", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    draw_rounded_rect(draw, (px1 + 83, py1), (55, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px1 + 110, py1 + 8), "REPORTED", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    py1 += 20
    # Headline - measure and ensure it fits
    draw_wrapped(draw, (px1 + 4, py1), "Jensen Huang returns to Nvidia HQ, shares surge 31%", F_SERIF_BOLD_16, fill=BLACK, max_width=panel_w - 12)
    py1 += 38
    # Body
    draw_wrapped(draw, (px1 + 4, py1), "First day back after board unanimously reinstated him Monday. Trump claims credit. Nasdaq +6.5%, S&P +4.7%. Huang tells staff: \"I'll be a better CEO.\"", F_SANS_9, fill=BLACK, max_width=panel_w - 12)
    py1 += 40
    # Sources
    draw_text(draw, (px1 + 4, py1), "Sources: Reuters · AP · Bloomberg", F_SANS_7, fill=GREY)

    # Panel 2: GAZA CHILDREN (fixed headline, redrawn illustration)
    px2 = margin + panel_w + panel_gap
    draw_london_hospital_scene(draw, px2, y + 20, panel_w - panel_gap, 115)
    py2 = y + 145
    draw_rounded_rect(draw, (px2 + 4, py2), (50, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px2 + 29, py2 + 8), "LONDON", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    draw_rounded_rect(draw, (px2 + 58, py2), (55, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px2 + 85, py2 + 8), "REPORTED", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    py2 += 20
    # FIXED HEADLINE - shortened to fit
    draw_wrapped(draw, (px2 + 4, py2), "Critically injured Gaza children flown to UK hospitals", F_SERIF_BOLD_16, fill=BLACK, max_width=panel_w - 12)
    py2 += 38
    draw_wrapped(draw, (px2 + 4, py2), "Israeli fire kills a Palestinian in Gaza; child dies of lead-poisoning complications. UK receives first medevac cohort.", F_SANS_9, fill=BLACK, max_width=panel_w - 12)
    py2 += 40
    draw_text(draw, (px2 + 4, py2), "Sources: BBC · Al Jazeera · The Times", F_SANS_7, fill=GREY)

    # Panel 3: SPACE/NUCLEAR
    px3 = margin + 2 * (panel_w + panel_gap)
    draw_orbit_scene(draw, px3, y + 20, panel_w - panel_gap, 115)
    py3 = y + 145
    draw_rounded_rect(draw, (px3 + 4, py3), (45, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px3 + 26, py3 + 8), "ORBIT", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    draw_rounded_rect(draw, (px3 + 53, py3), (55, 16), 3, fill=TAG_COLORS["REPORTED"])
    draw_text(draw, (px3 + 80, py3 + 8), "REPORTED", F_SANS_BOLD_7, fill=WHITE, anchor="mm")
    py3 += 20
    draw_wrapped(draw, (px3 + 4, py3), "NATO: space is security strategy as Russia readies nuclear orbiter", F_SERIF_BOLD_16, fill=BLACK, max_width=panel_w - 12)
    py3 += 38
    draw_wrapped(draw, (px3 + 4, py3), "German media: Moscow could orbit nuclear-armed spacecraft in December. NATO chief elevates space to core strategy.", F_SANS_9, fill=BLACK, max_width=panel_w - 12)
    py3 += 40
    draw_text(draw, (px3 + 4, py3), "Sources: Reuters · CNN · Investopedia", F_SANS_7, fill=GREY)

    y += lead_h + 6

    # ═══════════════════════════════════════
    # 7. THE DAY IN TEN (10 small cards, 2 rows of 5) - with real mini illustrations
    # ═══════════════════════════════════════
    draw_text(draw, (margin, y), "THE DAY IN TEN", F_SERIF_BOLD_16, fill=NAVY, anchor="la")
    y += 22

    ten_items = [
        (4, "ARMENIA", "Trump officials declare TRIPP project kickoff; Armenia unveils draft constitution for peace with Azerbaijan", "EUROPE", "flag"),
        (5, "UN", "Secretary-General demands AI safety framework within a year", "WORLD", "building"),
        (6, "POLAND", "Crashed objects classified as Soviet missiles", "EUROPE", "missile"),
        (7, "PAKISTAN", "4.0 quake near Afghan border; Lahore AQI 500+, 8 cities among worst", "ASIA-PACIFIC", "wave"),
        (8, "NEPAL", "India pledges €1.4bn for glacier flood rebuild", "ASIA-PACIFIC", "mountain"),
        (9, "PANAMA", "Govt and First Quantum resume Cobre Panama mine talks", "AMERICAS", "mine"),
        (10, "GERMANY", "~450 schools receive bomb threats by email", "EUROPE", "warning"),
        (11, "RUSSIA", "Murmansk governor Andrey Chibis detained on misappropriation", "EUROPE", "gavel"),
        (12, "CULTURE", "Ex-Mossad chief: Taylor Swift Vienna concerts saved from ISIS plot", "WORLD", "star"),
        (13, "CHINA", "Beijing ready to facilitate business visas for Indians", "ASIA-PACIFIC", "plane"),
    ]

    card_w = (content_w - 16) // 5
    card_h = 70
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            if idx >= len(ten_items):
                break
            num, region, headline, cat, icon_type = ten_items[idx]
            cx = margin + col * (card_w + 4)
            cy = y + row * (card_h + 4)

            # Card background
            draw_rounded_rect(draw, (cx, cy), (card_w, card_h), 4, fill=WHITE, outline=LIGHT_GREY)
            # Number
            draw_text(draw, (cx + 8, cy + 5), str(num), F_SERIF_BOLD_18, fill=RED, anchor="la")
            # Region tag
            rcolor = REGION_COLORS.get(cat, GREY)
            draw_rounded_rect(draw, (cx + 30, cy + 5), (55, 14), 3, fill=rcolor)
            draw_text(draw, (cx + 57, cy + 12), region, F_SANS_BOLD_7, fill=WHITE, anchor="mm")
            # Mini illustration - REAL flat colored shape
            icon_x = cx + card_w - 18
            icon_y = cy + 14
            draw_mini_icon(draw, icon_x, icon_y, icon_type, rcolor)
            # Headline
            draw_wrapped(draw, (cx + 8, cy + 26), headline, F_SANS_8, fill=BLACK, max_width=card_w - 16, line_spacing=1.15)
    y += 2 * (card_h + 4) + 6

    # ═══════════════════════════════════════
    # 8. BOTTOM: REGION CHIPS + ALSO ON (stacked vertically, no overlap)
    # ═══════════════════════════════════════
    # WHERE IT HAPPENED - region chips
    draw_text(draw, (margin, y), "WHERE IT HAPPENED", F_SERIF_BOLD_14, fill=NAVY, anchor="la")
    y += 20

    region_chips = [
        ("AMERICAS", "5", REGION_COLORS["AMERICAS"]),
        ("EUROPE", "6", REGION_COLORS["EUROPE"]),
        ("MIDDLE EAST", "5", REGION_COLORS["MIDDLE EAST"]),
        ("AFRICA", "4", REGION_COLORS["AFRICA"]),
        ("ASIA-PACIFIC", "7", REGION_COLORS["ASIA-PACIFIC"]),
        ("OCEANIA", "3", REGION_COLORS["OCEANIA"]),
        ("WORLD", "4", REGION_COLORS["WORLD"]),
    ]
    chip_total_w = content_w - 8
    chip_w = chip_total_w // 7
    chip_y = y
    for i, (name, count, color) in enumerate(region_chips):
        cx = margin + i * chip_w
        draw_rounded_rect(draw, (cx, chip_y), (chip_w - 2, 36), 4, fill=color)
        draw_text(draw, (cx + chip_w//2, chip_y + 10), name, F_SANS_BOLD_8, fill=WHITE, anchor="mm")
        draw_text(draw, (cx + chip_w//2, chip_y + 24), count + " stories", F_SANS_BOLD_10, fill=WHITE, anchor="mm")
    y = chip_y + 36 + 6  # advance past chips + gap

    # ALSO ON TUESDAY 24 NOVEMBER — 22 MORE STORIES (two columns, fitted)
    draw_text(draw, (margin, y), "ALSO ON TUESDAY 24 NOVEMBER — 22 MORE STORIES", F_SERIF_BOLD_13, fill=NAVY, anchor="la")
    y += 18

    also_items = [
        "14 Latvia PM refuses to restore ties with Russia",
        "15 Marine Le Pen names three Ukraine war scenarios, among them WWIII",
        "16 Iraqi leader arrives in Egypt on first official visit",
        "17 Trump targets Newsom in DOJ speech over commuting 548 death sentences",
        "18 Ex-Mississippi mayor jailed 37 months for bribery",
        "19 King Charles reached out to Meghan after Thomas Markle's arrest",
        "20 Dutch activist Jason Bhugwandass dies by euthanasia at 28",
        "21 Well-known Australian department store collapses; shoppers face precarious future",
        "22 Bangladesh garment workers reject pay offer; Yunus says Grameen branches targeted",
        "23 Syria-EU envoys fear focus on return of displaced persons",
        "24 Myanmar urged to follow intl law after ICJ ruling on Rohingya genocide",
        "25 UN warns Libya must not become battleground for Russia-Ukraine war",
        "26 Belarus opposition figure calls for talks with Lukashenko",
        "27 Kim says the North seeks protection, not control",
        "28 Lavrov voices concern over Lebanon, calls for national unity in Syria",
        "29 Vietnam to address trade surplus amid growing US pressure",
        "30 Taliban deploy officers to defend disappearing woodlands",
        "31 US seeks answers on Nvidia chip sales to China, Bessent says",
        "32 Russia plans $576m railway ferries for Kaliningrad to bypass Europe curbs",
        "33 Pauline Hanson faces biggest trial as Queensland state vote looms",
        "34 Thai protesters march 16 km to Bangchak refinery; court bails MP",
        "35 Anthropic shares fall as AI trade roars back on Huang's return",
    ]

    list_w = content_w
    col_w = list_w // 2
    line_h = 10  # tighter line height to fit in available space
    list_start_y = y
    for i, item in enumerate(also_items):
        col = i // 11
        row = i % 11
        ix = margin + col * col_w
        iy = list_start_y + row * line_h
        # Measure and truncate if needed
        max_w = col_w - 4
        w, _ = measure_text(draw, item, F_SANS_7)
        if w > max_w:
            # Truncate with ellipsis
            words = item.split()
            truncated = ""
            for word in words:
                test = (truncated + " " + word).strip() if truncated else word
                tw, _ = measure_text(draw, test + "…", F_SANS_7)
                if tw <= max_w:
                    truncated = test
                else:
                    break
            item = truncated + "…" if truncated else item[:max(w//6, 1)] + "…"
        draw_text(draw, (ix, iy), item, F_SANS_7, fill=BLACK, anchor="la")
    y = list_start_y + 11 * line_h + 4  # advance past list + gap

    # ═══════════════════════════════════════
    # 9. DATE CHECK BOX
    # ═══════════════════════════════════════
    dc_h = 40
    draw_rounded_rect(draw, (margin, y), (content_w, dc_h), 4, fill=(255, 240, 240), outline=RED, width=2)
    draw_text(draw, (margin + 8, y + 3), "DATE CHECK", F_SANS_BOLD_11, fill=DARK_RED, anchor="la")
    check_text = "Wires read up to 02:20 UTC. Every story on this page happened or was first reported on Tue 24 Nov 2026 in at least one time zone. Left out: COP31 collapse (Sun 22 Nov) · Russia 400-drone+110-missile barrage (19-20 Nov) · Kyiv toll 14 killed (22-23 Nov) · Ukraine sinks corvette Merkury (Sun 22 Nov) · Nvidia reinstates Huang (Mon 23 Nov) · Manchester concert evacuation (Sun 22 Nov) · SK education minister quits (Sun 22 Nov) · China sentences official Ma to death (Mon 23 Nov) · Russian strike near Kyiv presidential complex (Mon 23 Nov) · Houthi attacks Taiz (Mon 23 Nov) · IRGC tanker-mine claims Hormuz (7-20 Nov, unverified)"
    draw_wrapped(draw, (margin + 8, y + 18), check_text, F_SANS_6, fill=DARK_RED, max_width=content_w - 16, line_spacing=1.15)
    y += dc_h + 4

    # ═══════════════════════════════════════
    # 10. TAG LEGEND
    # ═══════════════════════════════════════
    legend_y = y
    draw_text(draw, (margin, legend_y), "TAG LEGEND", F_SANS_BOLD_10, fill=NAVY, anchor="la")
    legend_items = [
        ("ONGOING", "still developing"),
        ("REPORTED", "one source's claim, not yet confirmed"),
        ("CLAIM", "a party's claim, contested"),
        ("OFFICIALS SAY", "attributed, not verified"),
    ]
    lx = margin + 80
    for tag, desc in legend_items:
        color = TAG_COLORS[tag]
        draw_rounded_rect(draw, (lx, legend_y), (65, 14), 3, fill=color)
        draw_text(draw, (lx + 32, legend_y + 7), tag, F_SANS_BOLD_6, fill=WHITE, anchor="mm")
        draw_text(draw, (lx + 70, legend_y + 7), desc, F_SANS_7, fill=GREY, anchor="la")
        lx += 165
    y += 20

    # ═══════════════════════════════════════
    # 11. FOOTER
    # ═══════════════════════════════════════
    draw.line([(margin, y), (W - margin, y)], fill=LIGHT_GREY, width=1)
    y += 6
    draw_text(draw, (W//2, y), "Reuters · AP · CNN · BBC · Al Jazeera · The Times · Investopedia", F_SANS_8, fill=GREY, anchor="mm")
    y += 12
    draw_text(draw, (W//2, y), "make.fun  news-image-20261124  •  generated 2026-11-24", F_SANS_7, fill=LIGHT_GREY, anchor="mm")

    # ─── Save ───
    out_path = "/workspace/news-image-20261124/out/entry.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"Saved to {out_path}")

    # ─── Self-check ───
    import os
    size = os.path.getsize(out_path)
    print(f"File size: {size} bytes ({size/1024:.1f} KiB)")
    assert size <= 1048576, f"File too large: {size} > 1048576"

    # Verify dimensions
    with Image.open(out_path) as im:
        assert im.size == (1024, 1024), f"Wrong dimensions: {im.size}"
        assert im.mode == "RGB", f"Wrong mode: {im.mode}"
    print("Self-check: OK - 1024x1024 RGB, <=1MiB")

    return out_path

if __name__ == "__main__":
    generate()