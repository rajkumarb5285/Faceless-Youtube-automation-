import os
from app.config import settings

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_ass_karaoke_subtitles(
    words_timed: list[tuple[str, float, float]],
    out_path: str,
    palette: dict = None,
    font_name: str = "Arial"
) -> str:
    """
    Generate Advanced SubStation Alpha (.ass) subtitles with dynamic word-by-word
    karaoke highlighting matching Blueprint Section 6.9 and 12.
    Current spoken word is highlighted in accent color, while other words remain white.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    palette = palette or {}
    
    # Colors in ASS are &HAABBGGRR (hex format with alpha)
    # Default: Primary accent yellow/gold (&H0000D7FF), Normal text white (&H00FFFFFF), Outline black (&H00000000)
    primary_color = "&H00FFFFFF"      # White
    highlight_color = "&H0022D3EE"    # Vibrant Gold/Cyan highlight
    outline_color = "&H000B0F19"      # Dark border for contrast

    ass_header = f"""[Script Info]
Title: Faceless Multi-Agent Animated Captions
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},58,{primary_color},{highlight_color},{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,5,0,2,100,100,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    chunk_size = 4  # 3-5 words at a time (Blueprint 6.9)

    for i in range(0, len(words_timed), chunk_size):
        chunk = words_timed[i:i + chunk_size]
        if not chunk:
            continue
            
        chunk_start = chunk[0][1]
        chunk_end = chunk[-1][2]

        # For this chunk, generate dialogue lines where each word is highlighted during its duration
        for active_idx, (word, w_start, w_end) in enumerate(chunk):
            formatted_text_parts = []
            for j, (w_text, _, _) in enumerate(chunk):
                if j == active_idx:
                    # Highlight active word with color tag
                    formatted_text_parts.append(f"{{\\c{highlight_color}\\b1}}{w_text.upper()}{{\\c{primary_color}\\b1}}")
                else:
                    formatted_text_parts.append(w_text.upper())

            line_text = " ".join(formatted_text_parts)
            start_str = format_ass_time(w_start)
            end_str = format_ass_time(w_end)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

    content = ass_header + "\n".join(events) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return out_path
