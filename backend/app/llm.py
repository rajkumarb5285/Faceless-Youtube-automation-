import os
import re
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

SHARED_RULES = """You are part of an autonomous video studio for the channel described in CHANNEL_PROFILE.
Output only valid JSON matching the given schema. Never invent facts, statistics, quotes or URLs.
If evidence is missing, list it in the 'gaps' field. Write for a viewer who is smart but new to the topic.
"""

def extract_json(raw: str) -> str:
    """Extract valid JSON from potential markdown code fences or conversational text."""
    raw = raw.strip()
    # Match ```json ... ``` or ``` ... ```
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
    if m:
        return m.group(1).strip()
    
    # Try finding outer braces or brackets
    start_brace = raw.find('{')
    start_bracket = raw.find('[')
    
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = raw.rfind('}')
        if end_brace != -1:
            return raw[start_brace:end_brace + 1].strip()
    elif start_bracket != -1:
        end_bracket = raw.rfind(']')
        if end_bracket != -1:
            return raw[start_bracket:end_bracket + 1].strip()
            
    return raw

# Langfuse Observability Integration
langfuse_client = None
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    try:
        from langfuse import Langfuse
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST or "https://cloud.langfuse.com"
        )
        logger.info("Langfuse observability client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Langfuse client: {e}")

def log_langfuse_event(tag: str, model: str, system: str, user: str, output: str):
    if langfuse_client:
        try:
            langfuse_client.create_event(
                name=f"agent_{tag}",
                input={"tag": tag, "model": model, "system": system[:1000], "user": user[:2000]},
                output={"content": output[:3000]},
                metadata={"tag": tag, "model": model}
            )
            langfuse_client.flush()
        except Exception as e:
            logger.debug(f"Langfuse event logging failed: {e}")

def llm_call(model: str, system: str, user: str, tag: str = "agent") -> str:
    """
    Call Anthropic / OpenAI / Gemini or fall back to high-fidelity mock generators
    allowing full local dry runs out of the box. Automatically logs agent execution to Langfuse.
    """
    # 1. Anthropic Claude (Blueprint primary choice)
    if settings.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            resp = client.messages.create(
                model=model if "claude" in model else settings.DEFAULT_STRONG_MODEL,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            res_text = resp.content[0].text
            log_langfuse_event(tag, model, system, user, res_text)
            return res_text
        except Exception as e:
            logger.error(f"Anthropic call failed for tag {tag}: {e}")

    # 3. Groq (High-Speed Llama 3.3)
    if settings.GROQ_API_KEY:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            target_model = model if model in ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b") else (settings.DEFAULT_FAST_MODEL if "fast" in model else settings.DEFAULT_STRONG_MODEL)
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.4
            }
            for fallback_model in ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]:
                payload["model"] = fallback_model
                resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    res_text = data["choices"][0]["message"]["content"]
                    log_langfuse_event(tag, fallback_model, system, user, res_text)
                    return res_text
                elif resp.status_code == 429:
                    logger.warning(f"Groq 429 rate limit on {fallback_model}. Failing over to next model...")
                    continue
                else:
                    logger.error(f"Groq API returned {resp.status_code}: {resp.text}")
                    break
        except Exception as e:
            logger.error(f"Groq call failed for tag {tag}: {e}")

    # 4. Google Gemini
    if settings.GEMINI_API_KEY:
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": f"{system}\n\nUser:\n{user}"}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            resp = httpx.post(url, json=payload, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                res_text = data["candidates"][0]["content"]["parts"][0]["text"]
                log_langfuse_event(tag, "gemini-1.5-flash", system, user, res_text)
                return res_text
            else:
                logger.error(f"Gemini API returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Gemini call failed for tag {tag}: {e}")

    # 5. High-fidelity Mock responses for testing without API keys
    logger.info(f"Using deterministic structured mock response for tag: {tag}")
    res_text = mock_llm_response(tag, user)
    log_langfuse_event(tag, "mock-blueprint", system, user, res_text)
    return res_text

def mock_llm_response(tag: str, user: str) -> str:
    """Generate realistic mock JSON responses matching Blueprint Pydantic schemas."""
    if tag == "strategist":
        return json.dumps({
            "topic": "The Trillion-Dollar Energy Transition Bottleneck",
            "thesis": "High-voltage transformer lead times have reached 4 years, creating an invisible ceiling for renewable deployment and AI data centers that cannot be solved by capital alone.",
            "why_now": "Transformer wait times hit an all-time high of 210 weeks in late 2025/2026.",
            "audience_persona": "Tech & economics enthusiasts seeking concrete industrial reality checks.",
            "title_options": [
                "The 4-Year Wait Paralyzing the Entire AI Revolution",
                "Why the Global Power Grid Is Running Out of Transformers",
                "The Invisible Grid Bottleneck Nobody Is Talking About",
                "How a 19th-Century Component Stalled Clean Tech",
                "Inside the Global High-Voltage Transformer Shortage"
            ],
            "thumbnail_concept": "Massive smoking industrial transformer with yellow warning crane",
            "scores": {"demand": 9.2, "audience_fit": 8.8, "angle_originality": 9.5, "researchability": 8.5, "timely_balance": 9.0},
            "risks": ["Requires accurate engineering explanations of electrical core steel (GOES)."]
        })
    elif tag == "queries":
        return json.dumps({
            "queries": [
                "global high voltage transformer backlog data 2025 2026",
                "grain-oriented electrical steel shortage grid impact",
                "FERC transformer lead times report",
                "data center substation connection delays NERC",
                "Hitachi Energy Siemens Energy transformer order books",
                "copper winding supply chain power transformers",
                "substation equipment manufacturing expansion bottlenecks",
                "grid interconnection queue delays renewables 2026",
                "clean energy transition transformer equipment tariffs",
                "transformer manufacturing capacity workforce constraints"
            ]
        })
    elif tag == "extract":
        return json.dumps({
            "facts": [
                {"id": "", "fact": "Lead times for large power transformers (LPTs) exceed 150 to 210 weeks as of 2026.", "source_url": "https://gov.example.com/energy-grid-report", "tier": "T1", "date": "2026-02-14", "quote": "transformer wait times now routinely exceed four years"},
                {"id": "", "fact": "Grain-oriented electrical steel (GOES) production is dominated by only 5 global manufacturers.", "source_url": "https://example.org/materials-index", "tier": "T1", "date": "2025-11-20", "quote": "specialized core steel supply remains hyper-concentrated"},
                {"id": "", "fact": "Over 2,600 gigawatts of generation and storage capacity is currently stuck in US interconnection queues alone.", "source_url": "https://gov.example.com/lbl-queue-study", "tier": "T1", "date": "2026-01-10", "quote": "record 2600 gigawatts idling in interconnection requests"}
            ]
        })
    elif tag == "consolidate":
        return json.dumps({
            "facts": [
                {"id": "f1", "fact": "Lead times for large power transformers (LPTs) exceed 150 to 210 weeks as of 2026.", "source_url": "https://gov.example.com/energy-grid-report", "tier": "T1", "date": "2026-02-14", "quote": "transformer wait times now routinely exceed four years"},
                {"id": "f2", "fact": "Grain-oriented electrical steel (GOES) production is dominated by only 5 global manufacturers.", "source_url": "https://example.org/materials-index", "tier": "T1", "date": "2025-11-20", "quote": "specialized core steel supply remains hyper-concentrated"},
                {"id": "f3", "fact": "Over 2,600 gigawatts of generation and storage capacity is currently stuck in US interconnection queues alone.", "source_url": "https://gov.example.com/lbl-queue-study", "tier": "T1", "date": "2026-01-10", "quote": "record 2600 gigawatts idling in interconnection requests"}
            ],
            "contradictions": [],
            "gaps": ["Exact breakdown of lead times for European utilities vs North American utilities."],
            "suggested_outline_sections": ["The 4-Year Delivery Shock", "The Raw Material Chokehold: GOES Steel", "Why New Factories Take 3+ Years to Build", "The Hidden Standoff with AI Datacenters"]
        })
    elif tag == "verifier":
        return json.dumps({
            "claims": [
                {"id": "c1", "text": "Lead times for large power transformers exceed 150 to 210 weeks globally as of 2026.", "status": "verified", "sources": ["https://gov.example.com/energy-grid-report", "https://gov.example.com/lbl-queue-study"], "note": "Confirmed by both Department of Energy filings and independent transmission studies."},
                {"id": "c2", "text": "Grain-oriented electrical steel production is restricted to 5 primary global conglomerates.", "status": "verified", "sources": ["https://example.org/materials-index", "https://gov.example.com/energy-grid-report"], "note": "Cross-verified with metallurgy industrial registries."},
                {"id": "c3", "text": "Over 2,600 gigawatts of planned capacity is held in grid interconnection backlogs.", "status": "verified", "sources": ["https://gov.example.com/lbl-queue-study"], "note": "Confirmed in official 2026 Berkeley Lab review."}
            ]
        })
    elif tag == "planner":
        return json.dumps({
            "hook_idea": "Open directly with the physical reality: giant tech firms ordering solar farms with power lines that cannot connect until 2030.",
            "acts": [
                {"question": "Why is the grid bottleneck worse than semiconductor shortages?", "claim_ids": ["c1"], "twist": "You can spin up code in seconds, but high-voltage transformers take 4 years to press and test.", "open_loop": "So why can't manufacturers simply build more factories?", "word_budget": 280},
                {"question": "What is the single material choking the entire supply line?", "claim_ids": ["c2"], "twist": "It is not rare minerals—it is a specialized grain-oriented electrical steel made by barely five companies.", "open_loop": "Which creates a vicious bidding war with artificial intelligence.", "word_budget": 320},
                {"question": "How does this delay real-world power deployment?", "claim_ids": ["c3"], "twist": "2,600 gigawatts of energy are approved and financed, yet trapped waiting for a physical substation plug.", "open_loop": "Here is what happens to electricity prices when that logjam breaks.", "word_budget": 300}
            ],
            "payoff": "The clean energy and AI race will be decided not by chip fabrication or battery chemistry, but by who controls heavy electrical manufacturing.",
            "close": "If you want to see our deep-dive into the semiconductor water crisis, click here.",
            "retention_map": ["0:25 Sudden silence + map zoom", "0:55 Onscreen comparison chart reveal", "1:25 Direct challenge question to viewer"]
        })
    elif tag == "scriptwriter":
        return json.dumps({
            "title": "The 4-Year Wait Paralyzing the Entire AI Revolution",
            "scenes": [
                {"idx": 1, "narration": "Right now, if you order a utility-scale power transformer, delivery will not happen until 2030.", "on_screen_text": "LEAD TIME: 4+ YEARS", "visual_intent": "Huge industrial substation buzzing with high voltage sparks", "claim_ids": ["c1"], "pace": "normal", "pattern_interrupt": False},
                {"idx": 2, "narration": "Waiting periods for high voltage units have exploded past two hundred weeks across international grids.", "on_screen_text": "210 WEEKS DELAY", "visual_intent": "Aerial tracking shot across sprawling electric transmission pylons", "claim_ids": ["c1"], "pace": "normal", "pattern_interrupt": True},
                {"idx": 3, "narration": "The reason comes down to a hyper-specialized metal: grain-oriented electrical steel.", "on_screen_text": "GOES STEEL CHOKEPOINT", "visual_intent": "Close-up microscopic crystalline structure of electrical steel", "claim_ids": ["c2"], "pace": "normal", "pattern_interrupt": False},
                {"idx": 4, "narration": "Only five manufacturers on Earth have the metallurgical tooling to produce this grade at scale.", "on_screen_text": "5 GLOBAL MANUFACTURERS", "visual_intent": "World map highlighting the five specialized steel manufacturing hubs", "claim_ids": ["c2"], "pace": "slow", "pattern_interrupt": False},
                {"idx": 5, "narration": "Because of that single material choke, over twenty-six hundred gigawatts of power are now idling in regulatory backlogs.", "on_screen_text": "2,600 GW STUCK", "visual_intent": "Data visualization bar chart showing massive generation capacity trapped", "claim_ids": ["c3"], "pace": "fast", "pattern_interrupt": True},
                {"idx": 6, "narration": "Capital cannot accelerate heavy metallurgy overnight, meaning whoever controls transformer fabrication controls the pace of computation.", "on_screen_text": "PHYSICAL LIMITS", "visual_intent": "Contrast shot: clean modern server room next to heavy industrial forge", "claim_ids": ["c1", "c3"], "pace": "normal", "pattern_interrupt": False}
            ],
            "total_words": 150,
            "self_check_notes": "All claims linked to verified citations. No banned phrases present. Short punchy narration beats."
        })
    elif tag == "critic":
        return json.dumps({
            "scores": {
                "hook_strength": 9,
                "originality": 9,
                "clarity": 9,
                "pacing": 8,
                "voice_match": 9,
                "retention_beats": 8
            },
            "weakest_scenes": [],
            "rewrite_notes": []
        })
    elif tag == "visuals":
        return json.dumps({
            "shots": [
                {"scene_idx": 1, "visual_type": "stock", "query_or_spec": "electrical substation high voltage", "weight": 1.0, "motion": "zoom_in", "fallback": "text_card"},
                {"scene_idx": 2, "visual_type": "stock", "query_or_spec": "transmission towers power grid sunset", "weight": 1.0, "motion": "pan_left", "fallback": "chart"},
                {"scene_idx": 3, "visual_type": "motion_still", "query_or_spec": "industrial steel manufacturing facility forge", "weight": 1.0, "motion": "zoom_in", "fallback": "text_card"},
                {"scene_idx": 4, "visual_type": "chart", "query_or_spec": "world map 5 manufacturing countries", "weight": 1.0, "motion": "none", "fallback": "text_card"},
                {"scene_idx": 5, "visual_type": "chart", "query_or_spec": "bar chart 2600 GW interconnection queue backlog", "weight": 1.0, "motion": "none", "fallback": "text_card"},
                {"scene_idx": 6, "visual_type": "stock", "query_or_spec": "modern technology datacenter servers", "weight": 1.0, "motion": "pan_right", "fallback": "text_card"}
            ]
        })
    elif tag == "metadata":
        return json.dumps({
            "title_primary": "The 4-Year Wait Paralyzing the Entire AI Revolution",
            "title_variants": [
                "Why the Global Power Grid Has Run Out of Transformers",
                "The Heavy Metal Bottleneck That Will Delay AI to 2030"
            ],
            "description": "High-voltage transformer lead times have reached four years, stalling thousands of gigawatts of new clean energy and data centers.\n\nChapters:\n0:00 - The 210-Week Wait\n0:30 - The GOES Steel Monopoly\n1:00 - 2,600 Gigawatts Idling\n\nSources:\n- https://gov.example.com/energy-grid-report\n- https://gov.example.com/lbl-queue-study\n- https://example.org/materials-index",
            "chapter_scene_idx": [1, 3, 5],
            "chapter_titles": ["The 210-Week Wait", "The GOES Steel Monopoly", "2,600 Gigawatts Idling"],
            "hashtags": ["#AI", "#EnergyGrid", "#Economics"],
            "tags": ["artificial intelligence", "power grid", "transformers", "renewable energy", "substation"],
            "thumbnail_text_options": ["THE 4-YEAR CHOKE", "GRID LOCKED", "THE HIDDEN CEILING"],
            "pinned_comment": "Did you realize electrical steel was this concentrated? Share your thoughts below."
        })
    return "{}"
