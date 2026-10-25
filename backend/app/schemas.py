from typing import Literal, Optional, TypedDict, Any
from pydantic import BaseModel, Field, model_validator

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

class CreativeBrief(BaseModel):
    core_premise: str = ""
    central_question: str = ""
    narrative_form: str = "investigative"  # investigative, case_study, historical_reconstruction, scientific_explanation, chronological, problem_solving
    chosen_angle: str = ""
    key_insights: list[str] = Field(default_factory=list)
    target_audience_takeaway: str = ""
    what_makes_it_interesting: str = ""
    cliches_to_avoid: list[str] = Field(default_factory=list)

class Outline(BaseModel):
    hook_idea: str
    creative_brief: Optional[CreativeBrief] = None
    acts: list[Act]
    payoff: str
    close: str
    retention_map: list[str] = Field(default_factory=list)

class Scene(BaseModel):
    idx: int = 1
    narration: str
    on_screen_text: str = ""
    visual_intent: str = ""
    claim_ids: list[str] = Field(default_factory=list)
    pace: Literal["slow", "normal", "fast"] = "normal"
    pattern_interrupt: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_scene_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "idx" not in data and "scene_id" in data:
                data["idx"] = data["scene_id"]
            if not data.get("visual_intent") and data.get("visual_description"):
                data["visual_intent"] = data["visual_description"]
        return data

    @property
    def scene_id(self) -> int:
        return self.idx

    @property
    def visual_description(self) -> str:
        return self.visual_intent

class Script(BaseModel):
    title: str
    scenes: list[Scene]
    total_words: int = 0
    self_check_notes: str = ""
    central_question: Optional[str] = None
    narrative_angle: Optional[str] = None
    narrative_form: Optional[str] = None

class CriticReport(BaseModel):
    scores: dict[str, int]
    topic_fidelity_score: int = 8
    evidence_grounding_score: int = 8
    weakest_scenes: list[int] = Field(default_factory=list)
    rewrite_notes: list[str] = Field(default_factory=list)
    specific_critique: list[str] = Field(default_factory=list)

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

class QualityReport(BaseModel):
    passed: bool = False
    issues: list[str] = Field(default_factory=list)
    duration_actual: float = 0.0
    duration_expected: float = 0.0
    has_audio: bool = False
    has_video: bool = False
    resolution: str = "1920x1080"
    file_size_bytes: int = 0
    checks_performed: list[str] = Field(default_factory=list)
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    duration: Optional[float] = 0.0
    black_frames: Optional[int] = 0

class HumanApproval(BaseModel):
    required: bool = False
    status: Literal["pending", "approved", "rejected", "revision_requested"] = "pending"
    decision_by: Optional[str] = None
    feedback: Optional[str] = None
    timestamp: Optional[str] = None
    revised_script: Optional[Any] = None
    action: Optional[str] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = None

# LangGraph TypedDict state adhering to Phase Two specifications
class JobState(TypedDict, total=False):
    # Core Identifiers & Configurations
    job_id: str
    channel_id: str
    autonomy: int  # 0: Manual, 1: Script + Final Human Gate, 2: Gate on QA fail only, 3: Full autonomous
    custom_topic: Optional[str]
    custom_content: Optional[str]
    story_style: str  # 'stock_cinematic', 'cartoon_story', 'hybrid'
    language: str
    target_audience: str
    video_format: str
    target_duration: float

    # Research & Verification
    topic: dict
    research: dict
    research_sources: list[dict]
    claims: list[dict]
    verified_claims: list[dict]

    # Narrative, Scripting & Approval
    outline: dict
    script: dict
    script_revision: int
    critic: dict
    rewrite_count: int
    human_approval: dict

    # Visual Planning & Assets
    scene_plan: list[dict]
    shots: list[dict]
    visual_assets: list[dict]

    # Audio & Voiceover
    voice: dict
    narration_assets: list[dict]
    subtitles: dict

    # Video Assembly & QA
    render: dict
    render_artifacts: dict
    qa: dict
    quality_report: dict

    # Distribution & Analytics
    metadata: dict
    publication_status: dict
    video_id: str
    learnings: dict

    # Execution Observability & Recovery
    stage_status: dict[str, str]
    stage_durations: dict[str, float]
    errors: list[str]
    retry_counts: dict[str, int]
    checkpoint_info: dict

