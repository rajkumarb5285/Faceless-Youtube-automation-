"""
Automated Integration and Unit Tests for Hardened YouTube Automation Pipeline
Tests:
- JobState typing and validation
- Media Provider Manager & Circuit Breaker Ladder (Coverr -> Pixabay -> StoryCard)
- Critic Gate Routing (Pass / Rewrite / Escalate)
- Human Gate Routing and State Application (Approve / Reject / Revise)
- QA Gate Deterministic Stream Inspection & Retry Routing
- Durable File Checkpointer Serialization
- Publisher Idempotency Guard
- Analyst Metrics Aggregation
"""

import os
import sys
import time
import json
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.schemas import JobState, QualityReport, HumanApproval
from app.media_provider import MediaProviderManager, CoverrProvider, PixabayProvider
from app.graph import (
    route_after_critic,
    route_after_human,
    route_after_qa,
    DurableFileCheckpointer,
    app_graph
)
from app.nodes import human_gate_node, publisher, analyst
from app.db import db
from app.render import auto_checks


# ---------------------------------------------------------
# Test 1: State Typed Schema and QualityReport / HumanApproval
# ---------------------------------------------------------
def test_job_state_schema():
    state: JobState = {
        "topic": "Future of Quantum Computing",
        "target_audience": "Tech enthusiasts",
        "language": "en",
        "video_format": "landscape",
        "target_duration": 60,
        "critic_score": 85,
        "research_sources": ["https://nature.com/articles/quantum"],
        "verified_claims": [{"claim": "Quantum chips exist", "status": "verified"}],
        "script_revision": 1,
        "retry_counts": {"render": 0, "tts": 0},
        "stage_status": {"strategist": "completed"},
        "stage_durations": {"strategist": 1.2},
        "errors": []
    }
    assert state["topic"] == "Future of Quantum Computing"
    assert state["critic_score"] == 85
    assert len(state["verified_claims"]) == 1

def test_quality_report_pydantic():
    report = QualityReport(
        passed=True,
        has_video=True,
        has_audio=True,
        width=1920,
        height=1080,
        duration=62.5,
        black_frames=0,
        issues=[]
    )
    assert report.passed is True
    assert report.width == 1920
    assert report.black_frames == 0

def test_human_approval_pydantic():
    approval = HumanApproval(
        action="approve",
        reviewer="editor_in_chief",
        notes="Approved for visual production"
    )
    assert approval.action == "approve"
    assert approval.revised_script is None


# ---------------------------------------------------------
# Test 2: Media Provider Manager & Circuit Breaker Ladder
# ---------------------------------------------------------
def test_media_provider_circuit_breaker():
    manager = MediaProviderManager()
    coverr = manager.providers["coverr"]
    
    # Initially healthy
    assert coverr.is_available() is True
    
    # Trip circuit breaker
    coverr.trip_circuit_breaker(duration_seconds=5)
    assert coverr.is_available() is False
    assert coverr.failure_count == 1
    
    # Normal fallback ladder: Coverr disabled -> falls back to Pixabay
    with patch.object(manager.providers["pixabay"], "search_videos", return_value=[{"id": 1, "url": "http://pixabay.com/test.mp4"}]) as mock_pix:
        results = manager.search_media("ai technology", media_type="video")
        assert len(results) > 0
        assert results[0]["provider"] == "pixabay"
        mock_pix.assert_called_once()

def test_media_provider_deduplication_and_cache():
    manager = MediaProviderManager()
    with patch.object(manager.providers["pixabay"], "search_videos", return_value=[{"id": 42, "url": "http://pixabay.com/42.mp4"}]):
        res1 = manager.search_media("quantum computing", media_type="video")
        # Second call with same normalized query should hit cache
        res2 = manager.search_media("QUANTUM  COMPUTING  ", media_type="video")
        assert res1 == res2
        assert "quantum computing:video" in manager._cache


# ---------------------------------------------------------
# Test 3: Critic Gate Routing Logic
# ---------------------------------------------------------
def test_route_after_critic_high_score_high_autonomy():
    state: JobState = {
        "critic_score": 80,
        "critic_status": "pass",
        "autonomy": 2,
        "retry_counts": {}
    }
    assert route_after_critic(state) == "visuals"

def test_route_after_critic_low_score_rewrite():
    state: JobState = {
        "critic_score": 60,
        "critic_status": "revise",
        "autonomy": 2,
        "retry_counts": {"script_rewrite": 1}
    }
    assert route_after_critic(state) == "scriptwriter"

def test_route_after_critic_low_score_max_rewrites_escalates_to_human():
    state: JobState = {
        "critic_score": 60,
        "critic_status": "revise",
        "autonomy": 2,
        "retry_counts": {"script_rewrite": 3}
    }
    assert route_after_critic(state) == "human_review"

def test_route_after_critic_autonomy_level_1_always_human():
    state: JobState = {
        "critic_score": 95,
        "critic_status": "pass",
        "autonomy": 1,
        "retry_counts": {}
    }
    # Level 1 always mandates human gate
    assert route_after_critic(state) == "human_review"


# ---------------------------------------------------------
# Test 4: Human Gate Routing and Node
# ---------------------------------------------------------
def test_route_after_human():
    # 1. Approved -> visuals
    state_app: JobState = {"human_approval": {"action": "approve"}}
    assert route_after_human(state_app) == "visuals"

    # 2. Reject -> END
    state_rej: JobState = {"human_approval": {"action": "reject"}}
    assert route_after_human(state_rej) == "__end__"

    # 3. Revision requested -> scriptwriter
    state_rev: JobState = {"human_approval": {"action": "request_revision"}}
    assert route_after_human(state_rev) == "scriptwriter"

def test_human_gate_node_application():
    base_state: JobState = {
        "script": "Original draft.",
        "human_approval": {
            "action": "approve",
            "revised_script": "Human refined script.",
            "reviewer": "Alice"
        },
        "stage_status": {},
        "stage_durations": {}
    }
    updated = human_gate_node(base_state)
    assert updated["script"] == "Human refined script."
    assert updated["stage_status"]["human_gate"] == "approved"


# ---------------------------------------------------------
# Test 5: QA Gate Routing Logic
# ---------------------------------------------------------
def test_route_after_qa():
    # Passed QA
    state_pass: JobState = {
        "qa_status": "pass",
        "retry_counts": {"render": 0}
    }
    assert route_after_qa(state_pass) == "metadata"

    # Failed QA with retries remaining -> re-render
    state_fail: JobState = {
        "qa_status": "fail",
        "retry_counts": {"render": 1}
    }
    assert route_after_qa(state_fail) == "render"

    # Failed QA with max retries exceeded -> escalate to human review
    state_max_fail: JobState = {
        "qa_status": "fail",
        "retry_counts": {"render": 2}
    }
    assert route_after_qa(state_max_fail) == "human_review"


# ---------------------------------------------------------
# Test 6: Durable File Checkpointer Serialization
# ---------------------------------------------------------
def test_durable_file_checkpointer(tmp_path):
    ckpt_file = tmp_path / "test_checkpoints.pkl"
    saver1 = DurableFileCheckpointer(filepath=str(ckpt_file))
    
    # Store arbitrary checkpoint dictionary
    test_key = "thread_test_123"
    saver1.storage[test_key] = {"version": 1, "state": "paused_at_human"}
    saver1._save_to_disk()
    
    assert os.path.exists(ckpt_file)
    
    # Instantiate new checkpointer instance pointing to same file
    saver2 = DurableFileCheckpointer(filepath=str(ckpt_file))
    assert test_key in saver2.storage
    assert saver2.storage[test_key]["state"] == "paused_at_human"


# ---------------------------------------------------------
# Test 7: Publisher Idempotency Guard
# ---------------------------------------------------------
def test_publisher_idempotency():
    job_id = "test_job_idemp_999"
    state: JobState = {
        "job_id": job_id,
        "video_path": "data/renders/test_video.mp4",
        "metadata": {
            "title_primary": "Quantum Supremacy Explained",
            "description": "Educational breakdown of quantum computers.",
            "tags": ["quantum", "tech"]
        },
        "target_audience": "Tech Enthusiasts",
        "stage_status": {},
        "stage_durations": {}
    }
    
    # First publication
    res1 = publisher(state)
    assert res1["publication_status"]["status"] == "scheduled_private"
    assert res1["publication_status"]["platform"] == "youtube"
    
    # Second publication with same video / title
    res2 = publisher(state)
    assert res2["publication_status"]["status"] == "scheduled_private"
    assert res2["publication_status"].get("idempotent_cached") is True


# ---------------------------------------------------------
# Test 8: Analyst Metrics Aggregation
# ---------------------------------------------------------
def test_analyst_metrics():
    state: JobState = {
        "job_id": "test_job_analyst_1",
        "topic": "Renewable Energy",
        "scene_plan": [
            {"shot_number": 1, "duration": 5.0},
            {"shot_number": 2, "duration": 4.5},
            {"shot_number": 3, "duration": 6.0}
        ],
        "video_path": "data/renders/renewable.mp4",
        "target_duration": 15,
        "stage_durations": {"render": 12.4},
        "stage_status": {}
    }
    
    updated = analyst(state)
    metrics = updated.get("analytics_metrics", {})
    assert metrics.get("total_scenes") == 3
    assert metrics.get("total_cuts") == 2
    assert metrics.get("avg_cut_duration_sec") == pytest.approx(5.0, rel=0.1)
    assert updated["stage_status"]["analyst"] == "completed"


# ---------------------------------------------------------
# Test 9: Deterministic QA Stream Validation (ffprobe checks)
# ---------------------------------------------------------
def test_auto_checks_missing_file():
    report = auto_checks("non_existent_file_xyz123.mp4", 30.0)
    assert report["passed"] is False
    assert any("does not exist" in issue for issue in report["issues"])

def test_auto_checks_with_mocked_ffprobe():
    mock_probe = {
        "format": {"duration": "30.0"},
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080},
            {"codec_type": "audio", "channels": 2}
        ]
    }
    
    with patch("os.path.exists", return_value=True):
        with patch("os.path.getsize", return_value=5_000_000):
            with patch("subprocess.run") as mock_sub:
                # ffprobe stream inspection
                mock_sub.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_probe))
                report = auto_checks("mock_video.mp4", 30.0)
                assert report["passed"] is True
                assert report["has_video"] is True
                assert report["has_audio"] is True
