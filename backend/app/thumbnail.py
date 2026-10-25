import os
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

def generate_youtube_thumbnail(
    title_three_words: str,
    out_path: str,
    palette: dict = None,
    template_type: int = 1,
    accent_stat: str = "4+ YEARS"
) -> str:
    """
    Generate professional, high-CTR YouTube thumbnails using Pillow
    matching Blueprint Section 6.10:
    - 3-word punchy headline
    - High-contrast brand colors
    - Safe zone: avoids bottom-right 20% corner where YouTube timestamp sits (1280x720)
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    w, h = 1280, 720
    palette = palette or {
        "background": "#0F172A",
        "primary": "#3B82F6",
        "accent": "#F59E0B",
        "text": "#F8FAFC"
    }

    im = Image.new("RGB", (w, h), color=palette.get("background", "#0F172A"))
    draw = ImageDraw.Draw(im)

    try:
        font_huge = ImageFont.truetype("arial.ttf", 84)
        font_stat = ImageFont.truetype("arial.ttf", 98)
        font_badge = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font_huge = ImageFont.load_default()
        font_stat = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    words = title_three_words.upper().split()[:3]
    headline = " ".join(words)

    if template_type == 1:
        # Template 1: Split-Screen Contrast with Diagonal Brand Slice
        draw.polygon([(0, 0), (600, 0), (450, h), (0, h)], fill=palette.get("primary", "#3B82F6"))
        
        # Stat Accent Box on Left
        draw.rectangle([60, 160, 480, 240], fill="#000000")
        draw.text((80, 175), accent_stat, fill=palette.get("accent", "#F59E0B"), font=font_badge)

        # Main 3-word Headline on Right
        lines = words
        y = 200
        for line in lines:
            draw.text((620, y), line, fill=palette.get("text", "#F8FAFC"), font=font_huge)
            y += 105

    elif template_type == 2:
        # Template 2: Dark Cinematic Spotlight with Glowing Neon Bounding Border
        draw.rectangle([40, 40, w - 40, h - 40], outline=palette.get("accent", "#F59E0B"), width=8)
        draw.rectangle([80, 100, 440, 170], fill=palette.get("primary", "#3B82F6"))
        draw.text((100, 115), "URGENT REPORT", fill="#FFFFFF", font=font_badge)

        draw.text((100, 260), headline, fill=palette.get("text", "#F8FAFC"), font=font_huge)
        draw.text((100, 420), accent_stat, fill=palette.get("accent", "#F59E0B"), font=font_stat)

    else:
        # Template 3: Stat Shock Box (Large Number with Top Caution Ribbon)
        draw.rectangle([0, 0, w, 80], fill=palette.get("accent", "#F59E0B"))
        draw.text((60, 20), "CRITICAL GLOBAL BOTTLENECK", fill="#000000", font=font_badge)
        
        draw.text((80, 200), accent_stat, fill=palette.get("primary", "#3B82F6"), font=font_stat)
        draw.text((80, 360), headline, fill=palette.get("text", "#F8FAFC"), font=font_huge)

    # Note: Bottom-right safe zone (X: 1050-1280, Y: 600-720) is intentionally kept clean of text for YouTube timestamp

    im.save(out_path, quality=95)
    logger.info(f"Generated YouTube thumbnail template {template_type} at: {out_path}")
    return out_path
