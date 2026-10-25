"""
End-to-End Pipeline Verification Runner
Executes the full multi-agent flow locally as outlined in Blueprint Section 20.
"""

import os
import sys
import uuid
import logging

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.nodes import (
    strategist, researcher, verifier, planner, scriptwriter,
    critic, visual_planner, voice_director, render_video,
    qa_gate, metadata_agent
)
from app.schemas import JobState
from app.db import db
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestRunner")

def run_test():
    job_id = f"test_{uuid.uuid4().hex[:8]}"
    channel_id = "default"
    logger.info(f"=== Starting End-to-End Multi-Agent Pipeline Test [Job: {job_id}] ===")

    # Initialize State
    state: JobState = {
        "job_id": job_id,
        "channel_id": channel_id,
        "autonomy": 1,
        "rewrite_count": 0
    }

    # Step 1: Strategist (Topic & Angle Selection)
    logger.info("--> [1/10] Running Strategist...")
    res = strategist(state)
    state.update(res)
    logger.info(f"    Topic Selected: '{state['topic']['topic']}'")
    logger.info(f"    Thesis: {state['topic']['thesis']}")
    logger.info(f"    Top Title: {state['topic']['title_options'][0]}")

    # Step 2: Researcher (Information Gathering & Atomic Fact Extraction)
    logger.info("--> [2/10] Running Researcher...")
    res = researcher(state)
    state.update(res)
    facts_count = len(state['research']['facts'])
    logger.info(f"    Extracted {facts_count} atomic facts from sources.")

    # Step 3: Verifier (Fact-Checking & Claims Audit)
    logger.info("--> [3/10] Running Verifier...")
    res = verifier(state)
    state.update(res)
    verified = [c for c in state['claims'] if c['status'] == 'verified']
    weak = [c for c in state['claims'] if c['status'] == 'weak']
    logger.info(f"    Claims Audited: {len(verified)} verified, {len(weak)} weak.")

    # Step 4: Planner (Act Structure & Retention Map)
    logger.info("--> [4/10] Running Planner...")
    res = planner(state)
    state.update(res)
    logger.info(f"    Created {len(state['outline']['acts'])} acts with {len(state['outline']['retention_map'])} retention pattern interrupts.")

    # Step 5: Scriptwriter
    logger.info("--> [5/10] Running Scriptwriter...")
    res = scriptwriter(state)
    state.update(res)
    logger.info(f"    Script generated: '{state['script']['title']}' ({len(state['script']['scenes'])} scenes, {state['script']['total_words']} words).")

    # Step 6: Critic (Quality Gate 1)
    logger.info("--> [6/10] Running Critic (Quality Gate 1)...")
    res = critic(state)
    state.update(res)
    logger.info(f"    Critic Scores: {state['critic']['scores']}")
    logger.info(f"    Gate Passed: {state['critic']['pass']}")

    # Step 7: Visual Planner
    logger.info("--> [7/10] Running Visual Planner...")
    res = visual_planner(state)
    state.update(res)
    logger.info(f"    Planned {len(state['shots'])} visual shots.")

    # Step 8: Voice Director (TTS + Alignment)
    logger.info("--> [8/10] Running Voice Director...")
    res = voice_director(state)
    state.update(res)
    logger.info(f"    Voice track produced: {state['voice']['path']} (Total audio: {state['voice']['total']:.2f}s).")

    # Step 9: FFmpeg Video Renderer
    logger.info("--> [9/10] Rendering Video with FFmpeg & Captions...")
    res = render_video(state)
    state.update(res)
    logger.info(f"    Video rendered at: {state['render']['path']}")
    logger.info(f"    Subtitles generated at: {state['render']['srt']}")

    # Step 10: QA Gate (Quality Gate 2) & Metadata
    logger.info("--> [10/10] Running QA Gate & Metadata Agent...")
    qa_res = qa_gate(state)
    state.update(qa_res)
    meta_res = metadata_agent(state)
    state.update(meta_res)
    logger.info(f"    QA Passed: {state['qa']['passed']}")
    if state['qa']['issues']:
        logger.warning(f"    QA Issues: {state['qa']['issues']}")
    logger.info(f"    Primary Video Title: {state['metadata']['title_primary']}")
    logger.info(f"    Thumbnail Asset: {state['metadata']['thumb']}")

    logger.info("=== Multi-Agent Pipeline Test Successfully Finished! ===")
    print("\n-----------------------------------------------------------")
    print(f"[VIDEO] Generated Video: {os.path.abspath(state['render']['path'])}")
    print(f"[SUBTITLES] Subtitles File: {os.path.abspath(state['render']['srt'])}")
    print(f"[THUMBNAIL] Thumbnail: {os.path.abspath(state['metadata']['thumb'])}")
    print("-----------------------------------------------------------\n")

if __name__ == "__main__":
    run_test()
