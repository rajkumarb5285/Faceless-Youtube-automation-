from typing import Literal, Optional, TypedDict, Any
from pydantic import BaseModel, Field

class Topic(BaseModel):
    topic: str
    thesis: str
    why_now: str
    audience_persona: str
    title_options: list[str]
    thumbnail_concept: str
    scores: dict[str, float] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)

class QueryList(BaseModel):
    queries: list[str]

class Fact(BaseModel):
    id: str = ""
    fact: str
    source_url: str
    tier: Literal["T1", "T2", "T3"]
    date: Optional[str] = None
    quote: str = ""

class FactList(BaseModel):
    facts: list[Fact]

class Dossier(BaseModel):
    facts: list[Fact]
    contradictions: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    suggested_outline_sections: list[str] = Field(default_factory=list)

class Claim(BaseModel):
    id: str
    text: str
    status: Literal["verified", "weak", "rejected"]
    sources: list[str]
    note: str = ""

class ClaimsTable(BaseModel):
    claims: list[Claim]

class Act(BaseModel):
    question: str
    claim_ids: list[str]
    twist: str
    open_loop: str
    word_budget: int

class Outline(BaseModel):
    hook_idea: str
    acts: list[Act]
    payoff: str
    close: str
    retention_map: list[str]

class Scene(BaseModel):
    idx: int
    narration: str
    on_screen_text: str = ""
    visual_intent: str = ""
    claim_ids: list[str] = Field(default_factory=list)
    pace: Literal["slow", "normal", "fast"] = "normal"
    pattern_interrupt: bool = False

class Script(BaseModel):
    title: str
    scenes: list[Scene]
    total_words: int = 0
    self_check_notes: str = ""

class CriticReport(BaseModel):
    scores: dict[str, int]
    weakest_scenes: list[int] = Field(default_factory=list)
    rewrite_notes: list[str] = Field(default_factory=list)

class Shot(BaseModel):
    scene_idx: int = 0
    visual_type: str = "motion_still"
    query_or_spec: str = ""
    weight: float = 1.0  # share of the scene duration
    motion: str = "zoom_in"
    fallback: str = "text_card"

class ShotList(BaseModel):
    shots: list[Shot]

class Metadata(BaseModel):
    title_primary: str
    title_variants: list[str] = Field(default_factory=list)
    description: str
    chapter_scene_idx: list[int] = Field(default_factory=list)
    chapter_titles: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    thumbnail_text_options: list[str] = Field(default_factory=list)
    pinned_comment: str = ""

class ChannelProfile(BaseModel):
    id: str = Field(alias="_id", default="default")
    name: str = "Primary Explainer Channel"
    niche: str = "Technology & Global Trends"
    audience_personas: list[str] = Field(default_factory=lambda: [
        "Curious tech-savvy professionals aged 25-45 looking for deep systemic understanding"
    ])
    brand_voice: str = "Authoritative, analytical, engaging, conversational"
    banned_phrases: list[str] = Field(default_factory=lambda: [
        "in today's video", "without further ado", "let's dive in", "game-changer", "in conclusion", "buckle up"
    ])
    language_code: str = "en-US"  # or hi-IN, etc.
    youtube_lang: str = "en"
    script: str = "Latin"
    mixing_rule: str = "Pure English"
    tts_route: dict[str, Any] = Field(default_factory=lambda: {
        "provider": "mock",
        "voice": "standard_voice",
        "pace": 1.0
    })
    palette: dict[str, str] = Field(default_factory=lambda: {
        "primary": "#3B82F6",
        "accent": "#F59E0B",
        "background": "#0F172A",
        "text": "#F8FAFC"
    })
    font: str = "Noto Sans"
    pronunciations: dict[str, str] = Field(default_factory=dict)
    wpm: Optional[float] = 145.0
    timezone: str = "Asia/Kolkata"
    target_minutes: int = 8
    upload_schedule: list[str] = Field(default_factory=lambda: ["Tuesday 18:00", "Friday 18:00"])

# LangGraph TypedDict state
class JobState(TypedDict, total=False):
    job_id: str
    channel_id: str
    autonomy: int  # 0..3
    custom_topic: str
    custom_content: str
    story_style: str
    topic: dict
    research: dict
    claims: list
    outline: dict
    script: dict
    critic: dict
    rewrite_count: int
    shots: list
    voice: dict
    render: dict
    qa: dict
    metadata: dict
    video_id: str
    error: str
