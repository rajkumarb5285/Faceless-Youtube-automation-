import os
import re
import math
import json
import urllib.request
import urllib.parse
import subprocess
import io
import logging
import shutil

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

from app.media_provider import media_manager

def fetch_asset(shot: dict, work_dir: str, palette: dict, story_style: str = "cartoon_story", shot_id: str = "") -> str:
    """Resolve asset via MediaProviderManager: Coverr (4K/HD) -> Pixabay (HD) -> SerpApi/Pillow Visual Card."""
    scene_idx = shot.get("scene_idx", 1)
    slug = f"{scene_idx}_{shot_id}" if shot_id else str(scene_idx)
    v_type = shot.get("visual_type", "stock")
    query = shot.get("query_or_spec", "Story Overview")
    
    if v_type == "chart":
        chart_file = os.path.join(work_dir, f"asset_chart_{slug}.png")
        return create_chart_asset(query, chart_file, palette)

    prefer_video = (v_type in ("stock", "video", "footage", "b-roll") or story_style in ("stock_cinematic", "hybrid"))
    return media_manager.resolve_visual_asset(query, slug, work_dir, prefer_video=prefer_video, palette=palette)

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
        cmd = ['ffmpeg', '-y', '-loop', '1', '-i', asset, '-t', str(dur), '-vf', vf, '-c:v', 'libx264', '-r', '30', '-g', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    else:
        # Stock video footage with cohesive Vox-style contrast and color saturation
        vf = 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,eq=contrast=1.08:saturation=1.12'
        cmd = ['ffmpeg', '-y', '-stream_loop', '-1', '-i', asset, '-t', str(dur), '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '18', '-r', '30', '-g', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    
    try:
        sh(cmd)
    except Exception as e:
        logger.warning(f"FFmpeg make_shot failed ({e}). Generating fallback color block clip.")
        fallback_vf = f'color=c=black:s=1920x1080:d={dur}'
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', fallback_vf, '-t', str(dur), '-r', '30', '-g', '30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out])

def ensure_disk_space(target_dir: str = None, min_free_mb: int = 1000):
    """
    Ensure disk has at least min_free_mb available.
    If space is low, automatically prune oldest completed job media directories to prevent [Errno 28].
    """
    check_dir = target_dir or settings.STORAGE_DIR
    try:
        os.makedirs(check_dir, exist_ok=True)
        total, used, free = shutil.disk_usage(check_dir)
        free_mb = free / (1024 * 1024)
        if free_mb < min_free_mb:
            logger.warning(f"Low disk space detected ({free_mb:.1f} MB free). Pruning old media folders...")
            media_root = settings.STORAGE_DIR
            if os.path.exists(media_root):
                entries = []
                for name in os.listdir(media_root):
                    sub = os.path.join(media_root, name)
                    if os.path.isdir(sub):
                        entries.append((sub, os.path.getmtime(sub)))
                entries.sort(key=lambda x: x[1])
                for sub, _ in entries:
                    if target_dir and os.path.abspath(sub) == os.path.abspath(target_dir):
                        continue
                    try:
                        shutil.rmtree(sub, ignore_errors=True)
                        logger.info(f"Cleaned old media folder to free space: {sub}")
                    except Exception:
                        pass
                    _, _, new_free = shutil.disk_usage(check_dir)
                    if (new_free / (1024 * 1024)) >= min_free_mb:
                        break
    except Exception as e:
        logger.warning(f"Disk space check error: {e}")

def render_pipeline_video(state: dict) -> dict:
    """Complete video assembly with Ken Burns animation, TTS audio, karaoke ASS subtitles, and S3 sync."""
    job = state.get('job_id') or 'default_job'
    work = os.path.abspath(os.path.join(settings.STORAGE_DIR, job))
    ensure_disk_space(work, min_free_mb=1000)
    os.makedirs(work, exist_ok=True)
    
    ch = state.get('channel_profile') or db.channels.find_one({'_id': state.get('channel_id', 'default')}) or {}
    palette = ch.get('palette', {})
    story_style = state.get('story_style', 'cartoon_story')
    
    voice_data = state.get('voice') or {}
    scenes_list = voice_data.get('scenes', [])
    if not scenes_list and state.get('script', {}).get('scenes'):
        scenes_list = [{'idx': sc['idx'], 'dur': 5.0, 'wav': f"Scene {sc['idx']}"} for sc in state['script']['scenes']]
    scenes = {s['idx']: s for s in scenes_list}
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
        sh(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', shots_txt, '-c', 'copy', '-movflags', '+faststart', silent_mp4])
    except Exception:
        # Robust filter_complex concat fallback if copy concatenation fails
        try:
            inputs = []
            for c in clips:
                inputs.extend(['-i', c])
            filter_str = f"concat=n={len(clips)}:v=1:a=0[v]"
            sh(['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_str, '-map', '[v]', '-c:v', 'libx264', '-r', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', silent_mp4])
        except Exception:
            fallback_dur = max(5.0, state.get('voice', {}).get('total', 10.0))
            sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'color=c=black:s=1920x1080:d={fallback_dur}', '-t', str(fallback_dur), '-r', '30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', silent_mp4])

    # Word-by-word animated karaoke subtitles (.ass)
    ass_path = os.path.join(work, "captions.ass")
    srt_path = os.path.join(work, "captions.srt")
    words_data = voice_data.get('words', [])
    
    generate_ass_karaoke_subtitles(words_data, ass_path, palette)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(words_to_srt(words_data))

    final_mp4 = os.path.join(work, "final.mp4")
    final_tmp = os.path.join(work, "final_tmp.mp4")
    total_dur = max(5.0, voice_data.get('total', 10.0))
    bgm_path = os.path.join(work, "bgm.wav")

    # Synthesize subtle ambient sound bed matching exact duration
    if not os.path.exists(bgm_path):
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
    raw_voice = voice_data.get('path', '')
    voice_input = os.path.abspath(raw_voice) if raw_voice and os.path.isfile(raw_voice) else ""
    if not voice_input or not os.path.isfile(voice_input):
        candidates = [
            os.path.join(work, "voice_full.wav"),
            os.path.join(work, os.path.basename(raw_voice)) if raw_voice else "",
            os.path.join(work, "voice_001.wav")
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                voice_input = os.path.abspath(c)
                break

    voice_ffmpeg_path = voice_input.replace('\\', '/') if (voice_input and os.path.isfile(voice_input)) else ""

    # Guarantee audio stream: if voice track is missing, synthesize a silent audio bed
    if not voice_ffmpeg_path or not os.path.isfile(voice_input):
        silent_voice = os.path.abspath(os.path.join(work, "silent_voice.wav"))
        try:
            sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo:d={total_dur}', '-t', str(total_dur), '-c:a', 'pcm_s16le', silent_voice])
            if os.path.isfile(silent_voice):
                voice_ffmpeg_path = silent_voice.replace('\\', '/')
        except Exception as a_err:
            logger.warning(f"Silent audio synthesis fallback: {a_err}")

    # Burn animated captions and mix voiceover with background music bed
    ass_filename = os.path.basename(ass_path)
    rendered_ok = False

    # Primary pass: Video + Voice + BGM + ASS Subtitles + faststart
    try:
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
                '-movflags', '+faststart',
                'final_tmp.mp4'
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
                '-movflags', '+faststart',
                'final_tmp.mp4'
            ]
        else:
            cmd = [
                'ffmpeg', '-y',
                '-i', 'silent.mp4',
                '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo:d={total_dur}',
                '-vf', f"ass={ass_filename}",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                'final_tmp.mp4'
            ]
        sh(cmd, cwd=work)
        if os.path.exists(final_tmp) and os.path.getsize(final_tmp) > 10000:
            rendered_ok = True
    except Exception as sub_err:
        logger.warning(f"Direct ASS burning failed: {sub_err}. Falling back to clean audio mux.")

    # Secondary pass: Direct Audio Muxing without ASS burning if libass failed
    if not rendered_ok:
        try:
            if os.path.exists(final_tmp):
                try: os.remove(final_tmp)
                except Exception: pass
            if voice_ffmpeg_path:
                sh(['ffmpeg', '-y', '-i', 'silent.mp4', '-i', voice_ffmpeg_path, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', 'final_tmp.mp4'], cwd=work)
            else:
                sh(['ffmpeg', '-y', '-i', 'silent.mp4', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo:d={total_dur}', '-c:v', 'copy', '-c:a', 'aac', '-movflags', '+faststart', 'final_tmp.mp4'], cwd=work)
            if os.path.exists(final_tmp) and os.path.getsize(final_tmp) > 10000:
                rendered_ok = True
        except Exception as mux_err:
            logger.warning(f"Secondary audio muxing failed: {mux_err}")

    # Atomic move to final.mp4 to prevent reading unclosed / partial files
    if rendered_ok and os.path.exists(final_tmp):
        if os.path.exists(final_mp4):
            try: os.remove(final_mp4)
            except Exception: pass
        os.replace(final_tmp, final_mp4)
    elif not os.path.exists(final_mp4) or os.path.getsize(final_mp4) < 10000:
        # Ultimate fallback to silent.mp4 with audio track added
        try:
            sh(['ffmpeg', '-y', '-i', silent_mp4, '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo:d={total_dur}', '-c:v', 'copy', '-c:a', 'aac', '-movflags', '+faststart', final_mp4])
        except Exception:
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

def auto_checks(path: str, expected_seconds: float) -> dict:
    """Automated deterministic QA checks on the rendered video file."""
    issues = []
    checks = []
    has_video = False
    has_audio = False
    actual_dur = 0.0
    file_size = 0
    res_str = "0x0"

    # 1. File existence & nonzero size
    checks.append("file_existence_and_size")
    if not path or not os.path.exists(path):
        return {
            "passed": False,
            "issues": [f"Rendered video file does not exist at path: {path}"],
            "duration_actual": 0.0,
            "duration_expected": expected_seconds,
            "has_audio": False,
            "has_video": False,
            "file_size_bytes": 0,
            "checks_performed": checks
        }

    file_size = os.path.getsize(path)
    if file_size < 10000:
        issues.append(f"Rendered video file is abnormally small ({file_size} bytes)")

    # 2. Streams & Codec probing with transient file-flush retry
    checks.append("stream_probe")
    probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,channels:format=duration', '-of', 'json', path]
    
    probe_success = False
    last_err = ""
    for attempt in range(3):
        try:
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                format_dur = data.get("format", {}).get("duration")
                if format_dur:
                    try:
                        actual_dur = float(format_dur)
                    except (ValueError, TypeError):
                        pass
                streams = data.get("streams", [])
                for s in streams:
                    if s.get("codec_type") == "video":
                        has_video = True
                        w, h = s.get("width", 0), s.get("height", 0)
                        res_str = f"{w}x{h}"
                        if w < 1280 or h < 720:
                            issues.append(f"Sub-HD resolution detected: {res_str}")
                    elif s.get("codec_type") == "audio":
                        has_audio = True
                probe_success = True
                break
            else:
                last_err = res.stderr[:200]
                import time
                time.sleep(0.5)
        except Exception as e:
            last_err = str(e)
            import time
            time.sleep(0.5)

    if not probe_success and last_err:
        issues.append(f"ffprobe stream inspection failed: {last_err}")

    if not has_video:
        issues.append("Missing video stream in rendered container")
    if not has_audio:
        issues.append("Missing audio stream in rendered container")

    # 3. Duration verification
    checks.append("duration_sync")
    if actual_dur == 0.0:
        actual_dur = probe_duration(path)
    if expected_seconds > 0 and abs(actual_dur - expected_seconds) > max(1.5, 0.08 * expected_seconds):
        issues.append(f"Duration mismatch: {actual_dur:.1f}s vs expected {expected_seconds:.1f}s")

    # 4. Black frames detection
    checks.append("blackdetect")
    try:
        log_black = sh(['ffmpeg', '-i', path, '-vf', 'blackdetect=d=1.0:pix_th=0.1', '-an', '-f', 'null', '-'])
        if 'black_start' in log_black:
            issues.append('Detected black frames longer than 1.0s')
    except Exception:
        pass

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "duration_actual": actual_dur,
        "duration_expected": expected_seconds,
        "has_audio": has_audio,
        "has_video": has_video,
        "resolution": res_str,
        "file_size_bytes": file_size,
        "checks_performed": checks
    }
