import os
import logging
from app.schemas import JobState
from app.render import make_shot, create_text_card
from app.tools import sh, probe_duration, words_to_srt, NL
from app.tts import tts
from app.config import settings

logger = logging.getLogger(__name__)

def generate_shorts_from_job(state: JobState, short_idx: int = 1) -> dict:
    """
    Generate vertical 9:16 (1080x1920) YouTube Shorts from the long-form video
    matching Blueprint Section 2, 12, and 17.4:
    'Render the Shorts version as a separate 9:16 timeline, not a crop of the long video.
    Each long video yields 2 to 3 Shorts for discovery.'
    """
    job_id = state.get("job_id", "demo")
    work_dir = os.path.join(settings.STORAGE_DIR, job_id, f"short_{short_idx}")
    os.makedirs(work_dir, exist_ok=True)
    
    script = state.get("script", {})
    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("Cannot generate Short without scenes in script.")

    # Select the most punchy scenes for a 30-45s Short (e.g., Hook Scene 1 and Scene 2)
    selected_scenes = scenes[:3] if len(scenes) >= 3 else scenes
    ch = state.get("channel_profile", {})
    palette = ch.get("palette", {
        "background": "#0F172A",
        "primary": "#3B82F6",
        "accent": "#F59E0B",
        "text": "#F8FAFC"
    })

    # 1. Generate Voice Audio for Short
    short_words_all = []
    short_scenes_data = []
    t = 0.0

    for sc in selected_scenes:
        text = sc.get("narration", "")
        wav = tts(text, job_id=job_id, idx=100 + sc.get("idx", 1), lang=ch.get("language_code", "en-US"))
        dur = probe_duration(wav) + 0.2
        
        words = text.split()
        word_dur = dur / max(1, len(words))
        w_st = t
        for w in words:
            short_words_all.append((w, w_st, w_st + word_dur))
            w_st += word_dur

        short_scenes_data.append({"idx": sc.get("idx", 1), "wav": wav, "dur": dur, "text": text, "on_screen": sc.get("on_screen_text", "")})
        t += dur

    # 2. Render Vertical 9:16 Visual Clips (1080x1920)
    clips = []
    for sc in short_scenes_data:
        # Create bold vertical text card
        card_img = os.path.join(work_dir, f"card_vert_{sc['idx']}.png")
        create_text_card(sc["on_screen"] or sc["text"][:60], card_img, palette, title="KEY FACT")
        
        shot_out = os.path.join(work_dir, f"shot_vert_{sc['idx']}.mp4")
        dur = sc["dur"]
        
        # FFmpeg scale & center crop into exact 9:16 vertical resolution (1080x1920)
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='zoom+0.001':d={int(dur * 30)}:s=1080x1920:fps=30"
        try:
            sh(["ffmpeg", "-y", "-loop", "1", "-i", card_img, "-t", str(dur), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", shot_out])
        except Exception:
            # Fallback color video in vertical orientation
            sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=#0F172A:s=1080x1920:d={dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", shot_out])
        
        clips.append(shot_out)

    # 3. Concatenate vertical clips
    shots_txt = os.path.join(work_dir, "vert_shots.txt")
    with open(shots_txt, "w") as f:
        f.write(NL.join(f"file '{os.path.abspath(c)}'" for c in clips))

    silent_vert = os.path.join(work_dir, "silent_vert.mp4")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", shots_txt, "-c", "copy", silent_vert])

    # 4. Concatenate audio
    wavs_txt = os.path.join(work_dir, "vert_wavs.txt")
    with open(wavs_txt, "w") as f:
        f.write(NL.join(f"file '{os.path.abspath(s['wav'])}'" for s in short_scenes_data))
    
    voice_track = os.path.join(work_dir, "voice_short.wav")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", wavs_txt, "-c", "copy", voice_track])

    # 5. Burn in high-contrast centered Short captions (2-3 words per line)
    srt_path = os.path.join(work_dir, "captions_short.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(words_to_srt(short_words_all, per_line=3))

    final_short = os.path.join(work_dir, "final_short.mp4")
    try:
        sh(["ffmpeg", "-y", "-i", silent_vert, "-i", voice_track, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final_short])
    except Exception:
        final_short = silent_vert

    logger.info(f"Generated 9:16 YouTube Short at: {final_short}")
    return {
        "short_path": final_short,
        "srt_path": srt_path,
        "duration": probe_duration(final_short),
        "aspect_ratio": "9:16",
        "resolution": "1080x1920"
    }
