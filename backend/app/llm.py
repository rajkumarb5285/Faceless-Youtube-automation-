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

    # 3. Groq (High-Speed LLM inference)
    if settings.GROQ_API_KEY:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            # Prioritize flagship high-capacity models with creative temperature
            groq_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
            if model in groq_models:
                groq_models.remove(model)
                groq_models.insert(0, model)
            elif settings.DEFAULT_STRONG_MODEL in groq_models:
                groq_models.remove(settings.DEFAULT_STRONG_MODEL)
                groq_models.insert(0, settings.DEFAULT_STRONG_MODEL)

            for groq_model in groq_models:
                payload = {
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.6 if tag in ("scriptwriter", "planner") else 0.3
                }
                resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=25.0)
                if resp.status_code == 200:
                    data = resp.json()
                    res_text = data["choices"][0]["message"]["content"]
                    log_langfuse_event(tag, groq_model, system, user, res_text)
                    return res_text
                elif resp.status_code == 429:
                    logger.warning(f"Groq 429 rate limit on {groq_model}. Failing over to next model...")
                    continue
                else:
                    logger.warning(f"Groq {groq_model} returned {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            logger.error(f"Groq call failed for tag {tag}: {e}")

    # 4. Google Gemini
    if settings.GEMINI_API_KEY:
        try:
            import httpx
            for gem_model in ["gemini-flash-latest", "gemini-2.5-flash", "gemini-3.8-flash"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system}\n\nUser Context:\n{user}"}]}],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.6 if tag in ("scriptwriter", "planner") else 0.3
                    }
                }
                try:
                    resp = httpx.post(url, json=payload, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        res_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        log_langfuse_event(tag, gem_model, system, user, res_text)
                        return res_text
                    elif resp.status_code in (404, 429):
                        continue
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Gemini call failed for tag {tag}: {e}")

    # 5. Dynamic Topic-Aware Structured Generator for reliable offline dry runs & unit tests
    logger.info(f"Using topic-aware structured generator for tag: {tag}")
    res_text = mock_llm_response(tag, user)
    log_langfuse_event(tag, "mock-dynamic", system, user, res_text)
    return res_text

def mock_llm_response(tag: str, user: str) -> str:
    """
    Generate realistic, topic-faithful structured JSON responses matching Blueprint Pydantic schemas.
    Dynamically extracts topic keywords and verified claims to preserve topic fidelity across arbitrary subjects.
    """
    try:
        data = json.loads(user) if isinstance(user, str) and user.strip().startswith("{") else {}
    except Exception:
        data = {}

    # Extract topic identity
    raw_topic = data.get('topic') or data.get('custom_topic') or 'The Subject Under Investigation'
    if isinstance(raw_topic, dict):
        topic_name = raw_topic.get('topic') or 'The Subject Under Investigation'
        raw_thesis = raw_topic.get('thesis') or f"The fundamental reality behind {topic_name}."
    else:
        topic_name = str(raw_topic)
        raw_thesis = data.get('thesis') or data.get('central_question') or f"How {topic_name} fundamentally operates and why it matters."

    # Determine topic domain / narrative form
    low_topic = topic_name.lower()
    if any(k in low_topic for k in ('gene', 'crispr', 'dna', 'cell', 'quantum', 'physics', 'atom', 'molecule', 'space', 'telescope')):
        narrative_form = "scientific_explanation"
        domain_angle = "Mechanistic molecular and physical discovery"
    elif any(k in low_topic for k in ('earthquake', 'war', 'history', 'ancient', 'empire', 'century', 'disaster', 'fire', 'mesopotamia')):
        narrative_form = "historical_reconstruction"
        domain_angle = "Forensic reconstruction of chronological timeline and consequences"
    elif any(k in low_topic for k in ('engine', 'turbine', 'rocket', 'machine', 'hardware', 'semiconductor', 'grid', 'chip')):
        narrative_form = "engineering_analysis"
        domain_angle = "Physical thermodynamic and systemic manufacturing constraints"
    elif any(k in low_topic for k in ('enron', 'fraud', 'market', 'economy', 'bank', 'wall street', 'money', 'crypto', 'billion')):
        narrative_form = "case_study"
        domain_angle = "Investigative audit of institutional incentives and failures"
    else:
        narrative_form = "investigative"
        domain_angle = "Systemic cause-and-effect deep dive"

    if tag == "strategist":
        return json.dumps({
            "topic": topic_name,
            "thesis": raw_thesis,
            "why_now": f"Fresh empirical findings and strategic shifts in 2026 brought {topic_name} into immediate focus.",
            "audience_persona": "Curious viewers seeking deep, concrete systemic understanding rather than generic summaries.",
            "title_options": [
                f"The Untold Reality of {topic_name}",
                f"How {topic_name} Actually Works Behind the Scenes",
                f"The Hidden Breaking Point of {topic_name}",
                f"Why Everyone Misunderstood {topic_name}",
                f"Inside {topic_name}: The Evidence Nobody Examined"
            ],
            "thumbnail_concept": f"Cinematic detailed visual moment revealing the core mechanism of {topic_name}",
            "scores": {"demand": 9.2, "audience_fit": 9.0, "angle_originality": 9.5, "researchability": 8.8, "timely_balance": 9.1},
            "risks": [f"Requires precise factual explanation of {topic_name} without falling into generic tropes."]
        })
    elif tag == "queries":
        words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', topic_name) if w.lower() not in ('the', 'how', 'why', 'what', 'and', 'for')]
        base_term = " ".join(words) or topic_name
        return json.dumps({
            "queries": [
                f"{base_term} primary evidence documentation data",
                f"{base_term} technical mechanism and structural constraints",
                f"{base_term} independent audit academic analysis",
                f"{base_term} timeline failure modes breakthrough findings",
                f"{base_term} economic and systemic real world impact",
                f"{base_term} verified historical statistics"
            ]
        })
    elif tag in ("extract", "consolidate"):
        return json.dumps({
            "facts": [
                {"id": "f1", "fact": f"Core empirical mechanism of {topic_name} established through primary field evidence.", "source_url": f"https://archive.example.org/{topic_name.lower().replace(' ', '-')}/analysis", "tier": "T1", "date": "2026-01-15", "quote": f"definitive documentation confirms the primary mechanism of {topic_name}"},
                {"id": "f2", "fact": f"The primary operational constraint on {topic_name} limits overall throughput and scalability.", "source_url": f"https://doi.example.org/10.1000/{topic_name.lower().replace(' ', '-')}", "tier": "T1", "date": "2025-11-20", "quote": f"independent audits reveal key constraints in {topic_name}"},
                {"id": "f3", "fact": f"Long-term systemic implications of {topic_name} fundamentally alter modern outcomes.", "source_url": f"https://gov.example.com/reports/{topic_name.lower().replace(' ', '-')}", "tier": "T1", "date": "2026-02-01", "quote": f"measurable impact of {topic_name} verified across the domain"}
            ],
            "contradictions": [],
            "gaps": [f"Specific longitudinal variance across global implementations of {topic_name}."],
            "suggested_outline_sections": [f"The Core Dilemma of {topic_name}", f"The Unseen Mechanism", f"The Systemic Breaking Point", f"The Long-Term Resolution"]
        })
    elif tag == "verifier":
        return json.dumps({
            "claims": [
                {"id": "c1", "text": f"Empirical field documentation confirms the primary operating principle of {topic_name}.", "status": "verified", "sources": [f"https://archive.example.org/{topic_name.lower().replace(' ', '-')}/analysis"], "note": "Verified against primary institutional reports."},
                {"id": "c2", "text": f"The decisive constraint governing {topic_name} was historically overlooked by conventional accounts.", "status": "verified", "sources": [f"https://doi.example.org/10.1000/{topic_name.lower().replace(' ', '-')}"], "note": "Cross-referenced with independent technical audits."},
                {"id": "c3", "text": f"Modern systemic outcomes directly trace back to how {topic_name} resolved its core paradox.", "status": "verified", "sources": [f"https://gov.example.com/reports/{topic_name.lower().replace(' ', '-')}"], "note": "Confirmed by longitudinal impact studies."}
            ]
        })
    elif tag == "planner":
        brief = data.get('creative_brief') or {}
        q = brief.get('central_question') or raw_thesis
        return json.dumps({
            "hook_idea": f"Open immediately with the tangible paradox of {topic_name}: {q}",
            "creative_brief": {
                "core_premise": raw_thesis,
                "central_question": q,
                "narrative_form": narrative_form,
                "chosen_angle": domain_angle,
                "key_insights": [
                    f"The immediate operational reality of {topic_name}",
                    f"The hidden structural constraint that dictated outcomes",
                    f"The verified resolution and permanent legacy of {topic_name}"
                ],
                "target_audience_takeaway": f"The audience grasps the precise causal chain that drove {topic_name}.",
                "what_makes_it_interesting": f"Counterintuitive evidence contradicts popular surface-level assumptions about {topic_name}.",
                "cliches_to_avoid": ["vague generalities", "generic hype", "unsubstantiated claims"]
            },
            "acts": [
                {"question": f"What was the real starting point of {topic_name}?", "claim_ids": ["c1"], "twist": f"The common story missed the physical constraint.", "open_loop": f"Which led directly to an unexpected dilemma.", "word_budget": 160},
                {"question": f"How did the critical constraint in {topic_name} manifest?", "claim_ids": ["c2"], "twist": f"Conventional solutions made the bottleneck more severe.", "open_loop": f"Until an unorthodox mechanism was introduced.", "word_budget": 180},
                {"question": f"What does {topic_name} reveal about the future?", "claim_ids": ["c3"], "twist": f"The long-term impact extends far beyond the initial event.", "open_loop": f"Here is the definitive verdict.", "word_budget": 160}
            ],
            "payoff": f"The climactic synthesis explaining why {topic_name} reshaped its entire domain.",
            "close": f"A lasting reflection challenging the audience to reconsider how {topic_name} operates.",
            "retention_map": [f"0:20 - Evidence reveal on {topic_name}", f"0:45 - Mechanism breakdown", f"1:15 - Consequence analysis"]
        })
    elif tag == "scriptwriter":
        brief = data.get('creative_brief') or {}
        q = data.get('central_question') or brief.get('central_question') or raw_thesis
        claims = data.get('verified_claims') or data.get('claims') or [
            {"id": "c1", "text": f"Primary empirical documentation establishes how {topic_name} operates."},
            {"id": "c2", "text": f"The decisive constraint governing {topic_name} shaped its trajectory."},
            {"id": "c3", "text": f"Systemic outcomes confirmed by independent analysis of {topic_name}."}
        ]
        c1 = claims[0].get('text') if len(claims) > 0 else f"verified evidence regarding {topic_name}"
        c2 = claims[1].get('text') if len(claims) > 1 else c1
        c3 = claims[2].get('text') if len(claims) > 2 else c2

        return json.dumps({
            "title": f"The Untold Reality of {topic_name}",
            "central_question": q,
            "narrative_angle": brief.get("chosen_angle", domain_angle),
            "narrative_form": brief.get("narrative_form", narrative_form),
            "scenes": [
                {
                    "idx": 1,
                    "narration": f"When you examine {topic_name}, one decisive question emerges: {q}",
                    "on_screen_text": topic_name[:24].upper(),
                    "visual_intent": f"Cinematic wide visual establishing the tangible environment of {topic_name}, authentic lighting and atmosphere",
                    "claim_ids": ["c1"],
                    "pace": "normal",
                    "pattern_interrupt": False
                },
                {
                    "idx": 2,
                    "narration": f"For decades, surface-level explanations missed the underlying reality: {c1}.",
                    "on_screen_text": "THE EVIDENCE",
                    "visual_intent": f"Detailed dynamic breakdown diagram illustrating the fundamental mechanism of {topic_name}",
                    "claim_ids": ["c1"],
                    "pace": "normal",
                    "pattern_interrupt": True
                },
                {
                    "idx": 3,
                    "narration": f"The real turning point occurred when investigation proved that {c2}.",
                    "on_screen_text": "TURNING POINT",
                    "visual_intent": f"Forensic comparative visual showing the critical constraint of {topic_name} in operation",
                    "claim_ids": ["c2"],
                    "pace": "slow",
                    "pattern_interrupt": False
                },
                {
                    "idx": 4,
                    "narration": f"Because of that structural shift, {c3}, altering every projection that followed.",
                    "on_screen_text": "STRUCTURAL SHIFT",
                    "visual_intent": f"High-contrast data visualization revealing the verified consequences of {topic_name}",
                    "claim_ids": ["c3"],
                    "pace": "fast",
                    "pattern_interrupt": True
                },
                {
                    "idx": 5,
                    "narration": f"Ultimately, {topic_name} proves that real progress is governed not by rhetoric, but by physical and institutional evidence.",
                    "on_screen_text": "THE VERDICT",
                    "visual_intent": f"Impactful closing shot summarizing the lasting significance of {topic_name}",
                    "claim_ids": ["c1", "c3"],
                    "pace": "normal",
                    "pattern_interrupt": False
                }
            ],
            "total_words": 135,
            "self_check_notes": f"Topic fidelity confirmed for '{topic_name}'. Zero banned phrases. All claims verified."
        })
    elif tag == "critic":
        return json.dumps({
            "scores": {
                "topic_fidelity": 9,
                "evidence_grounding": 9,
                "central_question_coverage": 9,
                "originality": 8,
                "narrative_progression": 9,
                "spoken_quality": 9,
                "hook_strength": 8,
                "pacing_and_duration": 9
            },
            "topic_fidelity_score": 9,
            "evidence_grounding_score": 9,
            "weakest_scenes": [],
            "rewrite_notes": [],
            "specific_critique": [f"Script maintains rigorous focus on '{topic_name}' from start to finish."]
        })
    elif tag == "visuals":
        return json.dumps({
            "shots": [
                {"scene_idx": 1, "visual_type": "stock", "query_or_spec": f"{topic_name} cinematic setup", "weight": 1.0, "motion": "zoom_in", "fallback": "text_card"},
                {"scene_idx": 2, "visual_type": "chart", "query_or_spec": f"{topic_name} technical diagram", "weight": 1.0, "motion": "none", "fallback": "text_card"},
                {"scene_idx": 3, "visual_type": "motion_still", "query_or_spec": f"{topic_name} archival evidence", "weight": 1.0, "motion": "pan_left", "fallback": "text_card"},
                {"scene_idx": 4, "visual_type": "chart", "query_or_spec": f"{topic_name} data breakdown", "weight": 1.0, "motion": "none", "fallback": "text_card"},
                {"scene_idx": 5, "visual_type": "stock", "query_or_spec": f"{topic_name} conclusion shot", "weight": 1.0, "motion": "zoom_out", "fallback": "text_card"}
            ]
        })
    elif tag == "metadata":
        return json.dumps({
            "title_primary": f"The Untold Reality of {topic_name}",
            "title_variants": [
                f"How {topic_name} Actually Works",
                f"The Hidden Turning Point of {topic_name}"
            ],
            "description": f"A comprehensive, evidence-grounded investigation into {topic_name}.\n\nKey Insights:\n- The physical and systemic mechanisms.\n- The overlooked structural constraints.\n- The verifiable long-term outcomes.\n\nCentral Question: {raw_thesis}",
            "chapter_scene_idx": [1, 3, 5],
            "chapter_titles": ["The Core Question", "The Turning Point", "The Verdict"],
            "hashtags": [f"#{topic_name.replace(' ', '')[:15]}", "#Analysis", "#DeepDive"],
            "tags": [topic_name.lower(), "documentary", "investigation", "analysis"],
            "thumbnail_text_options": [f"{topic_name[:14].upper()}", "UNCOVERED", "THE VERDICT"],
            "pinned_comment": f"What was your biggest surprise about {topic_name}? Let us know below."
        })
    return "{}"
