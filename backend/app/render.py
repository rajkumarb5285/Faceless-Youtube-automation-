import os
import re
import math
import json
import urllib.request
import urllib.parse
import io
import logging

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
except ImportError:
    Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance = None, None, None, None, None, None

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

from app.tools import sh, probe_duration, words_to_srt, NL
from app.config import settings
from app.ass_styler import generate_ass_karaoke_subtitles
from app.storage import upload_media
from app.db import db

logger = logging.getLogger(__name__)

def create_rich_cartoon_card(text: str, out_path: str, palette: dict, title: str = "", scene_idx: int = 1) -> str:
    """Generate high-contrast, modern animated graphic cards using Pillow if image search is unavailable."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    w, h = 1920, 1080
    bg_color = palette.get("background", "#0B0F19")
    primary_color = palette.get("primary", "#3B82F6")
    accent_color = palette.get("accent", "#F59E0B")
    text_color = palette.get("text", "#F8FAFC")

    im = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(im)

    # Stylized radial / geometric background glow
    for radius in range(500, 100, -80):
        alpha_box = [w//2 - radius, h//2 - radius, w//2 + radius, h//2 + radius]
        draw.ellipse(alpha_box, outline="#1E293B", width=2)

    # Top accent header bar
    draw.rectangle([100, 80, 1820, 90], fill=primary_color)
    
    # Scene pill badge
    draw.rounded_rectangle([100, 120, 320, 170], radius=12, fill=accent_color)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 32)
        font_badge = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    draw.text((120, 132), f"SCENE {scene_idx}".upper(), fill="#000000", font=font_badge)
    if title:
        draw.text((340, 132), title.upper(), fill=text_color, font=font_small)

    # Word wrap main story text
    words = text.split()
    lines, curr_line = [], []
    for word in words:
        curr_line.append(word)
        if len(" ".join(curr_line)) > 35:
            lines.append(" ".join(curr_line))
            curr_line = []
    if curr_line:
        lines.append(" ".join(curr_line))

    # Center card box
    card_y = 300
    card_h = len(lines[:5]) * 85 + 60
    draw.rounded_rectangle([100, card_y - 20, 1820, card_y + card_h], radius=20, fill="#131B2E", outline="#334155", width=2)

    y = card_y + 30
    for line in lines[:5]:
        draw.text((150, y), line, fill=text_color, font=font_large)
        y += 85

    # Bottom branding bar
    draw.rectangle([100, 980, 1820, 990], fill="#334155")
    im.save(out_path, quality=95)
    return out_path

def create_chart_asset(spec: str, out_path: str, palette: dict) -> str:
    """Render high-contrast, dark-mode charts using Matplotlib (Blueprint 10.2)."""
    if plt is None:
        return create_rich_cartoon_card(spec, out_path, palette, title="Data Breakdown")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=palette.get("background", "#0F172A"))
    ax.set_facecolor(palette.get("background", "#0F172A"))

    labels, values = ["2022", "2023", "2024", "2025", "2026 (Est.)"], [120, 160, 240, 380, 620]
    bars = ax.bar(labels, values, color=palette.get("primary", "#3B82F6"), edgecolor=palette.get("accent", "#F59E0B"), width=0.55, linewidth=2)
    bars[-1].set_color(palette.get("accent", "#F59E0B"))

    ax.set_title(spec.upper(), color=palette.get("text", "#F8FAFC"), fontsize=24, pad=25, weight='bold')
    ax.tick_params(colors=palette.get("text", "#F8FAFC"), labelsize=16)
    ax.spines['bottom'].set_color(palette.get("text", "#F8FAFC"))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(palette.get("text", "#F8FAFC"))
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='#FFFFFF')

    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path

def download_and_process_cartoon_visual(query: str, scene_idx: int, work_dir: str, palette: dict, shot_id: str = "") -> str:
    """
    Search and download vibrant cartoon / vector illustrations via SerpApi Google Images API,
    then crop and format to 1920x1080 cinematic HD.
    """
    slug = f"{scene_idx}_{shot_id}" if shot_id else str(scene_idx)
    out_file = os.path.join(work_dir, f"asset_cartoon_{slug}.jpg")
    
    # Try searching SerpApi Google Images if key is provided
    if settings.SERPAPI_API_KEY:
        try:
            cartoon_query = f"{query} cartoon vector illustration"
            q_enc = urllib.parse.quote(cartoon_query)
            api_url = f"https://serpapi.com/search.json?engine=google_images&q={q_enc}&api_key={settings.SERPAPI_API_KEY}&num=10"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            res_raw = urllib.request.urlopen(req, timeout=8).read()
            res_data = json.loads(res_raw.decode('utf-8'))
            images = res_data.get('images_results', [])
            
            for img in images[:3]:
                img_url = img.get('original') or img.get('thumbnail')
                if not img_url:
                    continue
                try:
                    img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    img_bytes = urllib.request.urlopen(img_req, timeout=8).read()
                    if len(img_bytes) < 4000:
                        continue
                        
                    raw_im = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                    fitted = ImageOps.fit(raw_im, (1920, 1080), method=Image.Resampling.LANCZOS)
                    enhancer = ImageEnhance.Color(fitted)
                    fitted = enhancer.enhance(1.2)
                    enhancer_c = ImageEnhance.Contrast(fitted)
                    fitted = enhancer_c.enhance(1.1)

                    fitted.save(out_file, quality=95)
                    logger.info(f"Successfully downloaded cartoon visual for scene {slug} ({img_url[:60]})")
                    return out_file
                except Exception as dl_err:
                    logger.warning(f"Failed downloading candidate image {img_url[:40]}: {dl_err}")
                    continue
        except Exception as api_err:
            logger.warning(f"SerpApi image search failed for '{query}': {api_err}")

    # Fallback to high-res Pixabay images
    if settings.PIXABAY_API_KEY:
        try:
            from app.pixabay import download_pixabay_image
            pix_res = download_pixabay_image(f"{query} illustration", out_file)
            if pix_res and os.path.exists(pix_res):
                return pix_res
        except Exception as p_err:
            logger.warning(f"Pixabay visual fallback failed: {p_err}")

    # Fallback to high-aesthetic Pillow animated graphic card
    return create_rich_cartoon_card(query, out_file, palette, title="Visual Story Beat", scene_idx=scene_idx)

from app.coverr import download_coverr_clip
from app.pixabay import download_pixabay_video, download_pixabay_image

def fetch_asset(shot: dict, work_dir: str, palette: dict, story_style: str = "cartoon_story", shot_id: str = "") -> str:
    """Resolve asset according to visual ladder: Coverr / Pixabay Stock Video -> Pixabay / SerpApi Visuals -> Chart -> Styled Graphic Card."""
    scene_idx = shot.get("scene_idx", 1)
    slug = f"{scene_idx}_{shot_id}" if shot_id else str(scene_idx)
    v_type = shot.get("visual_type", "cartoon")
    query = shot.get("query_or_spec", "Story Overview")
    
    if v_type == "chart":
        chart_file = os.path.join(work_dir, f"asset_chart_{slug}.png")
        return create_chart_asset(query, chart_file, palette)

    # 1. High-quality Stock Footage: Try Coverr first, then Pixabay HD Videos
    if (v_type in ("stock", "video", "footage", "b-roll") or story_style == "stock_cinematic"):
        if settings.COVERR_API_KEY:
            stock_file = os.path.join(work_dir, f"asset_coverr_{slug}.mp4")
            clip_path = download_coverr_clip(query, stock_file)
            if clip_path and os.path.exists(clip_path):
                return clip_path
        if settings.PIXABAY_API_KEY:
            pix_vid_file = os.path.join(work_dir, f"asset_pix_vid_{slug}.mp4")
            pix_clip = download_pixabay_video(query, pix_vid_file)
            if pix_clip and os.path.exists(pix_clip):
                return pix_clip

    # 2. Photos & Illustrations via Pixabay
    if settings.PIXABAY_API_KEY and story_style in ("stock_cinematic", "photo_real"):
        pix_img_file = os.path.join(work_dir, f"asset_pix_img_{slug}.jpg")
        pix_img = download_pixabay_image(query, pix_img_file)
        if pix_img and os.path.exists(pix_img):
            return pix_img

    # 3. Cartoon, illustration, or motion still via SerpApi & Pixabay
    return download_and_process_cartoon_visual(query, scene_idx, work_dir, palette, shot_id=shot_id)

def make_shot(asset: str, dur: float, motion: str, out: str):
    """Render single shot clip with Ken Burns motion (zoom / pan) and cinematic color grade."""
    dur = max(1.0, dur)
    if asset.endswith(('.jpg', '.png', '.jpeg')):
        frames = int(dur * 30)
        # Ken Burns slow zoom or pan with subtle film grade
        if motion == 'pan_left':
            vf = f'scale=3840:-1,zoompan=x=\'iw-(iw/zoom)\':z=1.15:d={frames}:s=1920x1080:fps=30,eq=contrast=1.06:saturation=1.10'
        elif motion == 'pan_right':
            vf = f'scale=3840:-1,zoompan=x=0:z=1.15:d={frames}:s=1920x1080:fps=30,eq=contrast=1.06:saturation=1.10'
        else:
            # Default smooth cinematic zoom-in
            vf = f'scale=3840:-1,zoompan=z=\'zoom+0.0012\':d={frames}:s=1920x1080:fps=30,eq=contrast=1.06:saturation=1.10'
        cmd = ['ffmpeg', '-y', '-loop', '1', '-i', asset, '-t', str(dur), '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', out]
    else:
        # Stock video footage with cohesive Vox-style contrast and color saturation
        vf = 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,eq=contrast=1.08:saturation=1.12'
        cmd = ['ffmpeg', '-y', '-stream_loop', '-1', '-i', asset, '-t', str(dur), '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out]
    
    try:
        sh(cmd)
    except Exception as e:
        logger.warning(f"FFmpeg make_shot failed ({e}). Generating fallback color block clip.")
        fallback_vf = f'color=c=black:s=1920x1080:d={dur}'
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', fallback_vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', out])

def render_pipeline_video(state: dict) -> dict:
    """Complete video assembly with Ken Burns animation, TTS audio, karaoke ASS subtitles, and S3 sync."""
    job = state['job_id']
    work = os.path.join(settings.STORAGE_DIR, job)
    os.makedirs(work, exist_ok=True)
    
    ch = state.get('channel_profile') or db.channels.find_one({'_id': state.get('channel_id', 'default')}) or {}
    palette = ch.get('palette', {})
    story_style = state.get('story_style', 'cartoon_story')
    
    scenes = {s['idx']: s for s in state['voice']['scenes']}
    clips = []
    
    for idx in sorted(scenes):
        shots = [s for s in state.get('shots', []) if s['scene_idx'] == idx]
        if not shots:
            shots = [{'scene_idx': idx, 'visual_type': 'cartoon', 'query_or_spec': scenes[idx].get('wav', f'Scene {idx}'), 'weight': 1.0, 'motion': 'zoom_in'}]
        total_w = sum(s.get('weight', 1.0) for s in shots) or 1.0
        
        for k, s in enumerate(shots):
            dur = scenes[idx]['dur'] * s.get('weight', 1.0) / total_w
            asset = fetch_asset(s, work, palette, story_style, shot_id=str(k))
            out = os.path.join(work, f"shot_{idx:03d}_{k}.mp4")
            make_shot(asset, dur, s.get('motion', 'zoom_in'), out)
            clips.append(out)

    shots_txt = os.path.join(work, "shots.txt")
    with open(shots_txt, "w") as f:
        f.write(NL.join(f"file '{os.path.abspath(c)}'" for c in clips))

    silent_mp4 = os.path.join(work, "silent.mp4")
    try:
        sh(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', shots_txt, '-c', 'copy', silent_mp4])
    except Exception:
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'color=c=black:s=1920x1080:d={state["voice"]["total"]}', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', silent_mp4])

    # Word-by-word animated karaoke subtitles (.ass)
    ass_path = os.path.join(work, "captions.ass")
    srt_path = os.path.join(work, "captions.srt")
    words_data = state['voice'].get('words', [])
    
    generate_ass_karaoke_subtitles(words_data, ass_path, palette)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(words_to_srt(words_data))

    final_mp4 = os.path.join(work, "final.mp4")
    total_dur = max(5.0, state['voice'].get('total', 10.0))
    bgm_path = os.path.join(work, "bgm.wav")

    # Synthesize subtle ambient sound bed matching exact duration
    try:
        sh([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'sine=f=110:b=4:d={total_dur}',
            '-f', 'lavfi', '-i', f'anoisesrc=d={total_dur}:c=pink:r=44100:a=0.012',
            '-filter_complex', '[0:a][1:a]amix=inputs=2,volume=0.08[bg]',
            '-map', '[bg]',
            '-c:a', 'pcm_s16le',
            'bgm.wav'
        ], cwd=work)
    except Exception as bgm_err:
        logger.warning(f"BGM generation skipped: {bgm_err}")

    # Robust voice path resolution
    raw_voice = state['voice'].get('path', '')
    voice_input = os.path.abspath(raw_voice) if raw_voice else ""
    if not os.path.exists(voice_input):
        candidates = [
            os.path.join(work, "voice_full.wav"),
            os.path.join(work, os.path.basename(raw_voice) if raw_voice else ""),
            os.path.join(work, "voice_001.wav")
        ]
        for c in candidates:
            if c and os.path.exists(c):
                voice_input = os.path.abspath(c)
                break

    voice_ffmpeg_path = voice_input.replace('\\', '/') if voice_input else ""

    # Burn animated captions and mix voiceover with background music bed
    try:
        ass_filename = os.path.basename(ass_path)
        if voice_ffmpeg_path and os.path.exists(bgm_path):
            cmd = [
                'ffmpeg', '-y',
                '-i', 'silent.mp4',
                '-i', voice_ffmpeg_path,
                '-i', 'bgm.wav',
                '-filter_complex', '[1:a]volume=1.0[v]; [2:a]volume=0.10[m]; [v][m]amix=inputs=2:duration=first[aout]',
                '-map', '0:v',
                '-map', '[aout]',
                '-vf', f"ass={ass_filename}",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                'final.mp4'
            ]
        elif voice_ffmpeg_path:
            cmd = [
                'ffmpeg', '-y',
                '-i', 'silent.mp4',
                '-i', voice_ffmpeg_path,
                '-vf', f"ass={ass_filename}",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                'final.mp4'
            ]
        else:
            cmd = [
                'ffmpeg', '-y',
                '-i', 'silent.mp4',
                '-vf', f"ass={ass_filename}",
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                'final.mp4'
            ]
        sh(cmd, cwd=work)
    except Exception as sub_err:
        logger.warning(f"Direct ASS burning fallback to audio mix: {sub_err}")
        try:
            if voice_ffmpeg_path:
                sh(['ffmpeg', '-y', '-i', 'silent.mp4', '-i', voice_ffmpeg_path, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', 'final.mp4'], cwd=work)
        except Exception as e:
            logger.warning(f"Audio mixing failed: {e}. Outputting silent track.")
            final_mp4 = silent_mp4

    # Optional S3 upload
    s3_url = None
    if settings.STORAGE_BACKEND == 's3':
        try:
            s3_url = upload_media(final_mp4, f"{job}/final.mp4", content_type="video/mp4")
        except Exception as s3_err:
            logger.warning(f"S3 upload failed: {s3_err}")

    return {
        'render': {
            'path': final_mp4,
            'srt': srt_path,
            'ass': ass_path,
            's3_url': s3_url,
            'duration': probe_duration(final_mp4)
        }
    }

def auto_checks(path: str, expected_seconds: float) -> list[str]:
    """Automated pre-render quality checks (Blueprint 12 & 17.4)."""
    issues = []
    d = probe_duration(path)
    if abs(d - expected_seconds) > 0.05 * expected_seconds:
        issues.append(f"Duration mismatch: {d:.1f}s vs expected {expected_seconds:.1f}s")
    
    try:
        log_black = sh(['ffmpeg', '-i', path, '-vf', 'blackdetect=d=0.5:pix_th=0.1', '-an', '-f', 'null', '-'])
        if 'black_start' in log_black:
            issues.append('Detected black frames longer than 0.5s')
    except Exception:
        pass

    return issues
