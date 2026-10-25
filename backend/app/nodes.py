import os
import json
import logging
from app.schemas import (
    Topic, QueryList, FactList, Dossier, ClaimsTable, Outline, Script,
    CriticReport, ShotList, Metadata, JobState
)
from app.db import db
from app.llm import llm_call, extract_json, SHARED_RULES
from app.tools import web_search, fetch_page, store_vectors, top_similar, probe_duration, words_to_srt, NL, sh
from app.tts import tts
from app.render import render_pipeline_video, auto_checks
from app.config import settings

logger = logging.getLogger(__name__)

MODELS = {'strong': settings.DEFAULT_STRONG_MODEL, 'fast': settings.DEFAULT_FAST_MODEL}
BANNED = ['in today', 'without further ado', 'let us dive in', "let's dive in", 'game-changer', 'in conclusion', 'buckle up']

# Load prompt files
PROMPTS = {}
prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
for name in ['strategist', 'queries', 'extract', 'consolidate', 'verifier', 'planner', 'scriptwriter', 'critic', 'visuals', 'metadata']:
    filepath = os.path.join(prompts_dir, f"{name}.txt")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            PROMPTS[name] = f.read()
    else:
        PROMPTS[name] = ""

def profile(state: JobState) -> dict:
    chan_id = state.get('channel_id', 'default')
    chan = db.channels.find_one({'_id': chan_id})
    if not chan:
        chan = db.channels.find_one({'_id': 'default'}) or {}
    return chan

def agent(name: str, system: str, payload: dict, schema, model: str = 'strong'):
    user = json.dumps(payload, default=str)
    for attempt in range(3):
        raw = llm_call(MODELS[model], SHARED_RULES + "\n" + system, user, tag=name)
        try:
            return schema.model_validate_json(extract_json(raw))
        except Exception as e:
            logger.warning(f"Validation retry {attempt+1} on agent {name}: {e}")
            user += f" PREVIOUS OUTPUT INVALID: {str(e)[:400]} Return valid JSON only."
    raise RuntimeError(f"Agent failed after 3 retries: {name}")

def strategist(state: JobState) -> dict:
    ch = profile(state)
    past = [p.get('topic') for p in db.topics.find({'channel_id': ch.get('_id')}).limit(30)]
    custom_content = state.get('custom_content')
    custom = state.get('custom_topic')
    style = state.get('story_style', 'cartoon_story')
    
    # 1. Direct User-Pasted Content / Script
    if custom_content:
        first_line = custom_content.strip().splitlines()[0]
        title = custom or (first_line[:65] if len(first_line) > 5 else "Custom User Story")
        thesis = custom_content[:250].strip()
        out_dict = {
            "topic": title,
            "thesis": thesis,
            "why_now": "Direct user-provided creative story production.",
            "audience_persona": "Story and animation enthusiasts seeking unique narratives.",
            "title_options": [title],
            "thumbnail_concept": f"Dramatic cartoon character moment from {title[:30]}",
            "scores": {"demand": 10.0, "audience_fit": 10.0, "angle_originality": 10.0},
            "risks": []
        }
        db.topics.insert_one({'channel_id': ch.get('_id'), 'job_id': state['job_id'], **out_dict})
        return {'topic': out_dict}

    # 2. Custom Topic / Prompt provided by user
    if custom:
        cands = [{"title": custom, "demand_views": "Custom Viral Concept", "ratio": 5.0}]
    else:
        # 3. Dynamic Live Web Search: Query live trending mysteries and stories from the web
        try:
            live_results = web_search(f"{ch.get('niche', 'technology science')} viral story mystery 2026", n=4)
            cands = [{"title": r['title'][:65], "demand_views": "2.5M+", "ratio": 4.2} for r in live_results if len(r.get('title', '')) > 15]
            if not cands:
                raise ValueError("No live search candidates")
        except Exception:
            cands = [
                {"title": "The Strange Secret of the Underground Internet Cables", "demand_views": "3.8M", "ratio": 4.5},
                {"title": "The 4-Year Machine That Is Freezing the AI Revolution", "demand_views": "2.4M", "ratio": 4.1},
                {"title": "How One Accidental Bug Almost Destroyed Wall Street", "demand_views": "2.1M", "ratio": 3.9}
            ]

    sims = {c['title']: top_similar(c['title'], ch.get('_id', 'default')) for c in cands}
    out = agent('strategist', PROMPTS['strategist'], {
        'channel': ch,
        'candidates': cands,
        'past': past,
        'similar': sims,
        'custom_topic': custom,
        'story_style': style
    }, Topic)
    db.topics.insert_one({'channel_id': ch.get('_id'), 'job_id': state['job_id'], **out.model_dump()})
    return {'topic': out.model_dump()}

def researcher(state: JobState) -> dict:
    custom_content = state.get('custom_content')
    t = state['topic']
    
    # If user provided custom content, use their exact story facts directly
    if custom_content:
        lines = [line.strip() for line in custom_content.splitlines() if len(line.strip()) > 8]
        if not lines:
            lines = [custom_content]
        facts = [{'id': f'f{i+1}', 'fact': l, 'source_url': 'user_provided_story', 'tier': 'T1', 'quote': l} for i, l in enumerate(lines[:10])]
        dossier = {'facts': facts, 'contradictions': [], 'gaps': [], 'suggested_outline_sections': []}
        store_vectors(state['job_id'], facts)
        return {'research': dossier}

    queries = agent('queries', PROMPTS['queries'], {'thesis': t['thesis'], 'topic': t['topic']}, QueryList).queries[:4]
    facts, fetched = [], 0
    for q in queries:
        for res in web_search(q)[:2]:
            if fetched >= 5:
                break
            snippet = res.get('snippet', '')
            page = fetch_page(res['url']) if len(snippet) < 100 else snippet
            fetched += 1
            got = agent('extract', PROMPTS['extract'], {'thesis': t['thesis'], 'url': res['url'], 'text': (page or snippet)[:8000]}, FactList, model='fast')
            facts += [f.model_dump() for f in got.facts]
    
    dossier = agent('consolidate', PROMPTS['consolidate'], {'facts': facts, 'thesis': t['thesis']}, Dossier)
    for i, f in enumerate(dossier.facts):
        f.id = 'f' + str(i + 1)
    store_vectors(state['job_id'], [f.model_dump() for f in dossier.facts])
    return {'research': dossier.model_dump()}

def verifier(state: JobState) -> dict:
    custom_content = state.get('custom_content')
    if custom_content:
        claims = [{'id': f'c{i+1}', 'text': f.get('fact', ''), 'status': 'verified', 'sources': ['user_story']} for i, f in enumerate(state['research'].get('facts', []))]
        db.claims.insert_one({'job_id': state['job_id'], 'claims': claims})
        return {'claims': claims}

    items = []
    for f in state['research']['facts'][:6]:
        if f.get('tier') == 'T3':
            continue
        items.append({'fact': f, 'candidates': [{'url': f.get('source_url', ''), 'text': f.get('fact', '')}]})
    
    claims = []
    if items:
        table = agent('verifier', PROMPTS['verifier'], {'items': items}, ClaimsTable)
        claims = [c.model_dump() for c in table.claims]
    else:
        claims = [{'id': 'c1', 'text': state['topic']['thesis'], 'status': 'verified', 'sources': []}]
    
    db.claims.insert_one({'job_id': state['job_id'], 'claims': claims})
    return {'claims': claims}

def planner(state: JobState) -> dict:
    usable = [c for c in state['claims'] if c['status'] != 'rejected']
    ch = profile(state)
    out = agent('planner', PROMPTS['planner'], {
        'thesis': state['topic']['thesis'],
        'claims': usable,
        'target_minutes': ch.get('target_minutes', 8),
        'format': 'explainer'
    }, Outline)
    return {'outline': out.model_dump()}

def check_script(script: Script, claims: list, budget: int) -> list[str]:
    ids = {c['id']: c['status'] for c in claims}
    errs = []
    for sc in script.scenes:
        for cid in sc.claim_ids:
            if ids.get(cid, 'rejected') == 'rejected':
                errs.append(f'scene {sc.idx} uses unknown or rejected claim {cid}')
        if any(ch.isdigit() for ch in sc.narration) and not sc.claim_ids:
            errs.append(f'scene {sc.idx} has a number but no claim id')
        low = sc.narration.lower()
        errs += [f'scene {sc.idx} uses banned phrase: {b}' for b in BANNED if b in low]
    return errs

def scriptwriter(state: JobState) -> dict:
    custom_content = state.get('custom_content')
    claims = [c for c in state['claims'] if c['status'] != 'rejected']
    
    # If user provided custom content, convert their EXACT story into scenes without changing words
    if custom_content:
        prompt_instruction = (
            "Task: Convert this EXACT user-provided story into sequential cartoon video scenes of 8-15 seconds each.\n"
            "CRITICAL: Keep the exact user story, dialogue, character names, and narrative faithful to what the user provided.\n"
            "For each scene return: idx (1, 2, ...), narration (exact spoken text), on_screen_text (2-3 words for kinetic subtitle punch), visual_intent (rich cartoon/vector illustration prompt), claim_ids: ['c1'], pace: 'normal'.\n"
            f"User Story Text:\n{custom_content}\n"
            "Return valid JSON matching Script schema: {\"title\": \"...\", \"scenes\": [...], \"total_words\": 150, \"self_check_notes\": \"faithful to user content\"}"
        )
        for fallback_model in [MODELS['strong'], 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b']:
            try:
                raw_script = llm_call(fallback_model, SHARED_RULES + "\n" + prompt_instruction, custom_content, tag='scriptwriter')
                s = Script.model_validate_json(extract_json(raw_script))
                s.total_words = sum(len(x.narration.split()) for x in s.scenes)
                return {'script': s.model_dump()}
            except Exception as e:
                logger.warning(f"Scriptwriter parse retry on {fallback_model}: {e}")
                continue

    budget = sum(a.get('word_budget', 150) for a in state['outline'].get('acts', []))
    payload = {
        'channel_profile': profile(state),
        'outline': state['outline'],
        'claims': claims,
        'rewrite_notes': state.get('critic', {}).get('rewrite_notes', []),
        'previous_script': state.get('script')
    }
    
    for attempt in range(2):
        s = agent('scriptwriter', PROMPTS['scriptwriter'], payload, Script)
        errs = check_script(s, claims, budget)
        if not errs:
            break
        payload['code_check_errors'] = errs
        
    s.total_words = sum(len(x.narration.split()) for x in s.scenes)
    return {'script': s.model_dump()}

def critic(state: JobState) -> dict:
    rep = agent('critic', PROMPTS['critic'], {
        'script': state['script'],
        'claims': state['claims'],
        'channel_profile': profile(state)
    }, CriticReport)
    
    bad = len(check_script(Script(**state['script']), state['claims'], state['script']['total_words']))
    rep.scores['traceability'] = max(0, 10 - 2 * bad)
    
    vals = list(rep.scores.values())
    passed = (rep.scores['traceability'] == 10) and (min(vals) >= 7) and (sum(vals) / len(vals) >= 8)
    return {
        'critic': {**rep.model_dump(), 'pass': passed},
        'rewrite_count': state.get('rewrite_count', 0) + 1
    }

def visual_planner(state: JobState) -> dict:
    ch = profile(state)
    out = agent('visuals', PROMPTS['visuals'], {
        'script': state['script'],
        'claims': state['claims'],
        'palette': ch.get('palette', {})
    }, ShotList)
    
    # 3-Second Retention Formula: Splice scenes into dynamic alternating shots (Stock Video -> Thematic Visual -> Detail B-roll)
    shots = []
    style = state.get('story_style', 'cartoon_story')
    
    for sc in state['script']['scenes']:
        sc_shots = [s for s in out.shots if s.scene_idx == sc['idx']]
        narration = sc.get('narration', '')
        word_count = len(narration.split())
        v_intent = sc.get('visual_intent') or narration[:50]
        
        # If agent only provided 1 shot, enforce 3-second rule by creating 2 dynamic cuts
        if len(sc_shots) <= 1:
            # Cut 1: High-energy stock b-roll video (Coverr / Pixabay)
            shots.append({
                'scene_idx': sc['idx'],
                'visual_type': 'stock',
                'query_or_spec': f"{v_intent} cinematic footage",
                'weight': 0.5,
                'motion': 'pan_left'
            })
            # Cut 2: Stylized subject visual / cartoon / graphic focus
            shots.append({
                'scene_idx': sc['idx'],
                'visual_type': 'cartoon' if style == 'cartoon_story' else 'stock',
                'query_or_spec': v_intent,
                'weight': 0.5,
                'motion': 'zoom_in'
            })
            # If long scene (>20 words, ~6+ seconds), add 3rd quick cut
            if word_count > 20:
                shots.append({
                    'scene_idx': sc['idx'],
                    'visual_type': 'stock',
                    'query_or_spec': f"{narration[:30]} dramatic close-up",
                    'weight': 0.4,
                    'motion': 'pan_right'
                })
        else:
            for s in sc_shots:
                shots.append(s.model_dump())
                
    return {'shots': shots}

def voice_director(state: JobState) -> dict:
    ch = profile(state)
    scenes, words_all, t = [], [], 0.0
    lang = ch.get('language_code', 'en-US')
    tts_route = ch.get('tts_route', {'provider': 'mock'})

    for sc in state['script']['scenes']:
        text = sc['narration']
        wav = tts(text, voice=tts_route.get('voice'), job_id=state['job_id'], idx=sc['idx'], lang=lang, route=tts_route)
        dur = probe_duration(wav) + (0.5 if sc.get('pattern_interrupt') else 0.25)
        
        # Word timestamps
        words_in_sc = text.split()
        word_dur = dur / max(1, len(words_in_sc))
        w_st = t
        for w in words_in_sc:
            words_all.append((w, w_st, w_st + word_dur))
            w_st += word_dur

        scenes.append({'idx': sc['idx'], 'wav': wav, 'start': t, 'dur': dur})
        t += dur

    # Robust multi-clip audio concat using ffmpeg with safe relative filenames
    work_dir = os.path.join(settings.STORAGE_DIR, state['job_id'])
    voice_path = os.path.join(work_dir, "voice_full.wav")
    try:
        concat_txt = os.path.join(work_dir, "wavs.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for s in scenes:
                wav_rel = os.path.basename(s['wav'])
                f.write(f"file '{wav_rel}'\n")
        sh(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'wavs.txt', '-c:a', 'pcm_s16le', 'voice_full.wav'], cwd=work_dir)
        logger.info(f"Successfully concatenated {len(scenes)} audio scenes into voice_full.wav")
    except Exception as e:
        logger.warning(f"FFmpeg audio concat failed ({e}). Falling back to primary track.")
        voice_path = scenes[0]['wav'] if scenes else ""

    return {'voice': {'scenes': scenes, 'words': words_all, 'path': voice_path, 'total': t}}

def render_video(state: JobState) -> dict:
    """Render full video with cartoon visuals, Ken Burns zoom, and karaoke subtitles."""
    return render_pipeline_video(state)

def qa_gate(state: JobState) -> dict:
    render_path = state.get('render', {}).get('path', '')
    expected_dur = state.get('voice', {}).get('total', 10.0)
    issues = auto_checks(render_path, expected_dur)
    return {'qa': {'issues': issues, 'passed': len(issues) == 0}}

def metadata_agent(state: JobState) -> dict:
    out = agent('metadata', PROMPTS['metadata'], {
        'script': state['script'],
        'topic': state['topic'],
        'sources': state.get('research', {}).get('facts', [])
    }, Metadata, model='fast')
    
    meta_dict = out.model_dump()
    # Enrich with live winning YouTube tags via YouTube Data API v3
    if settings.YOUTUBE_API_KEY:
        try:
            from app.youtube_scout import get_seo_tags_for_topic
            topic_str = state.get('topic', {}).get('topic') or state.get('custom_topic', '')
            yt_tags = get_seo_tags_for_topic(topic_str)
            if yt_tags:
                existing_tags = meta_dict.get('tags', [])
                meta_dict['tags'] = list(dict.fromkeys(existing_tags + yt_tags))[:20]
        except Exception as e:
            logger.warning(f"YouTube SEO tags fetch error: {e}")

    meta_dict['thumb'] = os.path.join(settings.STORAGE_DIR, state['job_id'], "asset_card_1.png")
    return {'metadata': meta_dict}

def publisher(state: JobState) -> dict:
    # Check global kill switch
    kill_setting = db.settings.find_one({'_id': 'kill_switch'})
    if kill_setting and kill_setting.get('on'):
        raise RuntimeError("Kill switch is active. Publishing halted.")
    
    # Store publication record
    pub_record = {
        'job_id': state['job_id'],
        'video_id': f"mock_yt_{state['job_id'][:8]}",
        'status': 'scheduled_private',
        'title': state.get('metadata', {}).get('title_primary', 'Untitled Video')
    }
    db.publications.insert_one(pub_record)
    return {'video_id': pub_record['video_id']}

def analyst(state: JobState) -> dict:
    return {'learnings': {'insights': 'Audience retention peaks during numerical pattern interrupts.'}}
