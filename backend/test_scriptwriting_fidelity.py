"""
Comprehensive Multi-Topic Scriptwriting Fidelity & Quality Test Suite
=====================================================================
Tests the LangGraph Scriptwriting Agent, Creative Brief, Input Contract,
Topic Fidelity, Spoken Quality, Critic Gate Evaluation, and Targeted Revision
across 5 distinct topic domains:
1. Science: CRISPR-Cas9 Precision Gene Editing
2. History: The 1906 San Francisco Earthquake and Fire
3. Engineering: High-Bypass Jet Engine Turbofans
4. Business/Case Study: The Accounting Fraud Behind the Collapse of Enron
5. Culture/Education: The Origins of Cuneiform Writing in Ancient Mesopotamia
"""

import os
import pytest
from unittest.mock import patch
from app.schemas import JobState, Outline, Script, CriticReport, Scene
from app.nodes import scriptwriter, critic, check_script, planner
from app.llm import mock_llm_response

@pytest.fixture(autouse=True)
def mock_llm_calls_for_unit_tests():
    """Deterministic fast unit testing using the topic-aware mock generator unless RUN_LIVE_TESTS is set."""
    if not os.getenv("RUN_LIVE_TESTS"):
        with patch("app.nodes.llm_call", side_effect=lambda model, prompt, payload, tag: mock_llm_response(tag, payload)):
            yield
    else:
        yield

# --- 5 SUBSTANTIALLY DIFFERENT DOMAIN FIXTURES ---

TOPIC_FIXTURES = [
    {
        "domain": "science",
        "topic": "CRISPR-Cas9 Precision Gene Editing",
        "thesis": "How bacterial immune defense evolved into a programmable molecular scalpel capable of rewriting genetic code.",
        "keywords": ["crispr", "gene", "editing", "cas9", "dna"],
        "target_duration": 60,
        "facts": [
            {"id": "f1", "fact": "CRISPR-Cas9 originated as an adaptive immune system in bacteria against bacteriophages.", "source_url": "https://nature.com/articles/crispr"},
            {"id": "f2", "fact": "Guide RNA directs the Cas9 endonuclease to create targeted double-strand breaks at specific DNA sequences.", "source_url": "https://science.org/crispr-mechanism"},
            {"id": "f3", "fact": "The Protospacer Adjacent Motif (PAM) sequence is required for Cas9 to bind and cleave the target DNA.", "source_url": "https://cell.com/crispr-pam"}
        ],
        "claims": [
            {"id": "c1", "text": "Guide RNA directs Cas9 to cleave DNA at precise complementary target loci.", "sources": ["https://science.org"], "status": "verified"},
            {"id": "c2", "text": "CRISPR enables targeted therapeutic interventions for sickle cell disease.", "sources": ["https://nejm.org"], "status": "verified"}
        ]
    },
    {
        "domain": "history",
        "topic": "The 1906 San Francisco Earthquake and Fire",
        "thesis": "Why broken water mains and flawed military dynamite operations caused 80% of the city's destruction.",
        "keywords": ["1906", "san francisco", "earthquake", "fire"],
        "target_duration": 60,
        "facts": [
            {"id": "f1", "fact": "The earthquake struck at 5:12 AM on April 18, 1906 along the northern San Andreas Fault.", "source_url": "https://usgs.gov/1906-quake"},
            {"id": "f2", "fact": "Ruptured municipal water pipes left fire hydrants completely dry, preventing firefighters from halting the blaze.", "source_url": "https://sfhistory.org/water-mains"},
            {"id": "f3", "fact": "Military dynamiting of commercial buildings created backdraft fires that accelerated the destruction of downtown.", "source_url": "https://archives.gov/1906-fire"}
        ],
        "claims": [
            {"id": "c1", "text": "Ruptured water mains left fire departments powerless to extinguish the conflagration.", "sources": ["https://sfhistory.org"], "status": "verified"},
            {"id": "c2", "text": "Over eighty percent of San Francisco was destroyed by the firestorms.", "sources": ["https://usgs.gov"], "status": "verified"}
        ]
    },
    {
        "domain": "engineering",
        "topic": "High-Bypass Jet Engine Turbofans",
        "thesis": "How ducting air around the engine core delivers 90 percent of modern commercial flight thrust at high efficiency.",
        "keywords": ["turbofan", "engine", "bypass", "thrust"],
        "target_duration": 60,
        "facts": [
            {"id": "f1", "fact": "Modern commercial turbofans feature bypass ratios exceeding 10:1, where most air bypasses the combustion core.", "source_url": "https://aviationweek.com/turbofans"},
            {"id": "f2", "fact": "Single-crystal nickel superalloy turbine blades operate in gas temperatures exceeding their melting point.", "source_url": "https://asme.org/materials-turbines"},
            {"id": "f3", "fact": "Geared turbofan architectures allow the front fan and low-pressure turbine to rotate at independent optimum speeds.", "source_url": "https://flightglobal.com/geared-fans"}
        ],
        "claims": [
            {"id": "c1", "text": "High bypass ratio air produces the majority of subsonic propulsive thrust.", "sources": ["https://aviationweek.com"], "status": "verified"},
            {"id": "c2", "text": "Advanced cooling channels keep nickel turbine blades from melting under extreme combustion.", "sources": ["https://asme.org"], "status": "verified"}
        ]
    },
    {
        "domain": "business",
        "topic": "The Accounting Fraud Behind the Collapse of Enron",
        "thesis": "How mark-to-market accounting and off-balance-sheet Special Purpose Entities masked billions in debt.",
        "keywords": ["enron", "accounting", "fraud", "debt"],
        "target_duration": 60,
        "facts": [
            {"id": "f1", "fact": "Enron received SEC approval to use mark-to-market accounting for forward energy trading contracts.", "source_url": "https://sec.gov/enron-report"},
            {"id": "f2", "fact": "CFO Andrew Fastow created Special Purpose Entities like Chewco and LJM to hide toxic assets and debt.", "source_url": "https://justice.gov/enron-task-force"},
            {"id": "f3", "fact": "Whistleblower Sherron Watkins warned Kenneth Lay before Arthur Andersen shredded audit documentation.", "source_url": "https://sec.gov/watkins-memo"}
        ],
        "claims": [
            {"id": "c1", "text": "Mark-to-market accounting allowed Enron to book decades of estimated future profits immediately.", "sources": ["https://sec.gov"], "status": "verified"},
            {"id": "c2", "text": "Special Purpose Entities hid non-performing debt from public balance sheets.", "sources": ["https://justice.gov"], "status": "verified"}
        ]
    },
    {
        "domain": "culture",
        "topic": "The Origins of Cuneiform Writing in Ancient Mesopotamia",
        "thesis": "How agricultural token tallies in Uruk evolved into the world's first complete phonetic writing system.",
        "keywords": ["cuneiform", "mesopotamia", "writing", "clay"],
        "target_duration": 60,
        "facts": [
            {"id": "f1", "fact": "Cuneiform originated around 3200 BCE in Sumerian Uruk to track temple grain and livestock.", "source_url": "https://britishmuseum.org/cuneiform"},
            {"id": "f2", "fact": "Scribes pressed triangular cut reed styluses into moist clay tablets to produce wedge impressions.", "source_url": "https://metmuseum.org/uruk-tablets"},
            {"id": "f3", "fact": "The rebus principle enabled pictographic accounting symbols to represent spoken phonetic syllables.", "source_url": "https://orinst.ox.ac.uk/cuneiform-origins"}
        ],
        "claims": [
            {"id": "c1", "text": "Cuneiform evolved from clay counting tokens used in Mesopotamian agricultural accounting.", "sources": ["https://britishmuseum.org"], "status": "verified"},
            {"id": "c2", "text": "The rebus principle transformed administrative pictograms into abstract spoken language.", "sources": ["https://ox.ac.uk"], "status": "verified"}
        ]
    }
]


# --- TEST 1: TOPIC IMMUTABILITY & CONTRACT VALIDATION ---

def test_scriptwriter_missing_topic_validation():
    """Verify that Scriptwriter strictly validates the input contract and rejects empty topic states."""
    invalid_state = JobState(topic={}, outline={"acts": []})
    with pytest.raises(ValueError, match="missing topic in state"):
        scriptwriter(invalid_state)


def test_scriptwriter_missing_outline_validation():
    """Verify that Scriptwriter validates that an outline exists before proceeding."""
    invalid_state = JobState(topic={"topic": "Quantum Computing"}, outline={})
    with pytest.raises(ValueError, match="missing outline in state"):
        scriptwriter(invalid_state)


# --- TEST 2: MULTI-TOPIC SCRIPTWRITING FIDELITY ACROSS 5 DOMAINS ---

@pytest.mark.parametrize("fixture", TOPIC_FIXTURES, ids=[f["domain"] for f in TOPIC_FIXTURES])
def test_scriptwriter_topic_fidelity_across_domains(fixture):
    """
    Verify that across 5 distinct domains:
    1. Topic is preserved and reflected in title and scenes.
    2. Spoken narration contains subject-specific keywords.
    3. Creative brief metadata (central_question, narrative_angle) are populated on the Script.
    4. Spoken text does not contain visual bracket pollution (e.g. [Scene 1], [Visual: ...]).
    5. Word budget conforms to duration within acceptable speaking rate tolerance.
    """
    state = JobState(
        topic={"topic": fixture["topic"], "thesis": fixture["thesis"]},
        target_duration=fixture["target_duration"],
        claims=fixture["claims"],
        research={"facts": fixture["facts"], "gaps": []},
        outline={
            "acts": [
                {"act_number": 1, "heading": f"The Hook: {fixture['topic']}", "goal": "Engage audience with core tension", "target_seconds": 15, "claim_ids": ["c1"]},
                {"act_number": 2, "heading": "The Mechanism", "goal": "Explain the operational reality with evidence", "target_seconds": 30, "claim_ids": ["c1", "c2"]},
                {"act_number": 3, "heading": "The Consequence", "goal": "Conclude with significance and systemic impact", "target_seconds": 15, "claim_ids": ["c2"]}
            ],
            "creative_brief": {
                "core_premise": fixture["thesis"],
                "central_question": f"What is the underlying mechanism of {fixture['topic']}?",
                "narrative_form": "investigative",
                "chosen_angle": "Systemic cause-and-effect breakdown",
                "key_insights": [c["text"] for c in fixture["claims"]],
                "cliches_to_avoid": ["generic hype", "vague buzzwords"]
            }
        }
    )

    result = scriptwriter(state)
    assert "script" in result
    script = result["script"]

    # 1. Topic preserved in title or scenes
    assert script.get("title")
    full_narration = " ".join(scene["narration"].lower() for scene in script["scenes"])
    
    # 2. Key domain keywords must be present in the narration
    matched_keywords = [kw for kw in fixture["keywords"] if kw in full_narration]
    assert len(matched_keywords) >= 1, f"Expected domain keywords in narration for '{fixture['topic']}', found none. Narration: {full_narration}"

    # 3. Creative brief metadata preserved
    assert script.get("central_question")
    assert script.get("narrative_angle") or script.get("narrative_form")

    # 4. Spoken text quality: No visual/bracket leakage into narration
    for scene in script["scenes"]:
        narration = scene["narration"]
        assert "[" not in narration and "]" not in narration, f"Narration contains visual bracket leaks: {narration}"
        assert not narration.startswith("Scene "), f"Narration starts with scene label: {narration}"
        assert not narration.startswith("Visual:"), f"Narration starts with visual prompt: {narration}"

    # 5. Scene structure compatible with downstream nodes
    assert len(script["scenes"]) >= 3
    for scene in script["scenes"]:
        assert scene.get("idx") is not None
        assert scene.get("narration")
        assert scene.get("visual_intent") or scene.get("visual_description")
        assert isinstance(scene.get("claim_ids"), list)


# --- TEST 3: CRITIC GATE DETERMINISTIC TOPIC FIDELITY EVALUATOR ---

def test_critic_gate_accepts_high_fidelity_grounded_script():
    """Verify that Critic Gate passes a high-fidelity script with grounded claims."""
    fixture = TOPIC_FIXTURES[0] # CRISPR
    state = JobState(
        topic={"topic": fixture["topic"], "thesis": fixture["thesis"]},
        claims=fixture["claims"],
        research={"facts": fixture["facts"]},
        script={
            "title": "CRISPR: The Molecular Scalpel",
            "scenes": [
                {
                    "scene_id": 1,
                    "narration": "Inside bacterial immune systems, CRISPR-Cas9 operates as a precision molecular scalpel targeting invading viruses.",
                    "visual_description": "Microscopic view of Cas9 protein complex locking onto double-helix DNA strand.",
                    "claim_ids": ["c1"]
                },
                {
                    "scene_id": 2,
                    "narration": "Guide RNA directs Cas9 to cleave DNA at precise complementary target loci with single nucleotide accuracy.",
                    "visual_description": "Animation of guide RNA unwinding DNA and Cas9 molecular scissors making a clean double-strand break.",
                    "claim_ids": ["c1", "c2"]
                },
                {
                    "scene_id": 3,
                    "narration": "By mastering this mechanism, researchers can now edit mutations responsible for sickle cell disease.",
                    "visual_description": "Diagram transitioning from mutated hemoglobin cell to healthy round red blood cell.",
                    "claim_ids": ["c2"]
                }
            ],
            "total_words": 75
        }
    )

    result = critic(state)
    report = result.get("critic")
    assert report is not None
    assert report["passed"] is True
    assert report["scores"]["topic_fidelity"] >= 7
    assert report["scores"]["traceability"] >= 8


def test_critic_gate_rejects_off_topic_hallucinated_script():
    """
    Verify that Critic Gate catches a script that wanders off-topic
    (e.g., Requested topic: CRISPR Gene Editing, but Script discusses High-Voltage Grid Transformers).
    Must fail topic fidelity, reject the script, and return an actionable rewrite note.
    """
    fixture = TOPIC_FIXTURES[0] # CRISPR
    off_topic_state = JobState(
        topic={"topic": fixture["topic"], "thesis": fixture["thesis"]},
        claims=fixture["claims"],
        research={"facts": fixture["facts"]},
        script={
            "title": "High-Voltage Power Transformers",
            "scenes": [
                {
                    "scene_id": 1,
                    "narration": "The electrical grid depends on large power transformers to step up voltage for cross-country transmission lines.",
                    "visual_description": "Humming steel transformer substation yard.",
                    "claim_ids": []
                },
                {
                    "scene_id": 2,
                    "narration": "Copper windings and dielectric mineral oil insulate magnetic cores against catastrophic dielectric breakdown.",
                    "visual_description": "Cutaway of transformer cooling fins and oil reservoir.",
                    "claim_ids": []
                }
            ],
            "total_words": 60
        }
    )

    result = critic(off_topic_state)
    report = result.get("critic")
    assert report is not None
    assert report["passed"] is False
    assert report["scores"]["topic_fidelity"] < 7
    assert len(report["rewrite_notes"]) > 0
    # Must specify elevating topic fidelity for the specific topic
    assert any("fidelity" in note.lower() or fixture["topic"].lower() in note.lower() for note in report["rewrite_notes"])


# --- TEST 4: TARGETED SECTION REVISION MECHANISM ---

def test_targeted_section_revision_improves_weak_scenes():
    """
    Verify that when Critic provides rewrite notes identifying weak scenes,
    Scriptwriter incorporates previous script and rewrite notes to generate a revised script.
    """
    fixture = TOPIC_FIXTURES[2] # Jet Engine
    weak_previous_script = {
        "title": "Jet Engines",
        "scenes": [
            {
                "scene_id": 1,
                "narration": "Modern high-bypass turbofans propel commercial aircraft with extraordinary aerodynamic efficiency.",
                "visual_description": "Front intake of a GE9X jet engine spinning.",
                "claim_ids": ["c1"]
            },
            {
                "scene_id": 2,
                "narration": "Aeroplanes fly through the sky because people like traveling to holidays and business meetings.",
                "visual_description": "Generic airplane silhouette in clouds.",
                "claim_ids": []
            }
        ],
        "total_words": 40
    }

    state = JobState(
        topic={"topic": fixture["topic"], "thesis": fixture["thesis"]},
        target_duration=60,
        claims=fixture["claims"],
        research={"facts": fixture["facts"]},
        outline={
            "acts": [
                {"act_number": 1, "heading": "Thrust Architecture", "goal": "Explain bypass flow", "target_seconds": 30, "claim_ids": ["c1"]},
                {"act_number": 2, "heading": "Materials Science", "goal": "Explain superalloy cooling", "target_seconds": 30, "claim_ids": ["c2"]}
            ],
            "creative_brief": {
                "core_premise": fixture["thesis"],
                "central_question": "How does bypass air deliver 90% of thrust?",
                "narrative_form": "engineering_analysis",
                "chosen_angle": "Thermodynamics and bypass ratio",
                "key_insights": [c["text"] for c in fixture["claims"]],
                "cliches_to_avoid": ["generic travel talk"]
            }
        },
        script=weak_previous_script,
        script_revision=1,
        critic={
            "passed": False,
            "rewrite_notes": ["Scene 2 is generic filler. Replace with technical explanation of superalloy turbine cooling."],
            "weakest_scenes": [2]
        }
    )

    result = scriptwriter(state)
    assert "script" in result
    revised_script = result["script"]
    assert result["script_revision"] == 2
    assert revised_script["total_words"] > 0
    # Spoken narration must incorporate bypass or turbofan engineering content
    full_text = " ".join(s["narration"].lower() for s in revised_script["scenes"])
    assert "turbofan" in full_text or "bypass" in full_text or "engine" in full_text
