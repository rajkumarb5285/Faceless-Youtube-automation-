import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db import db
from app.graph import app_graph
from app.worker import run_job_async, resume_job
from app.schemas import ChannelProfile
from app.config import settings
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Faceless YouTube Multi-Agent Studio API",
    version="1.0.0",
    description="Automated multi-agent YouTube production pipeline built with LangGraph, FastAPI, and FFmpeg."
)

# Enable CORS for frontend Vite dev server & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve media directory for video and thumbnail previews
app.mount("/media", StaticFiles(directory=settings.STORAGE_DIR), name="media")

@app.get("/")
def read_root():
    return {
        "studio": "Faceless YouTube Multi-Agent Studio",
        "status": "online",
        "version": "1.0.0",
        "autonomy_level": settings.AUTONOMY_LEVEL
    }

# --- Channels API ---
@app.get("/channels")
def list_channels():
    return list(db.channels.find())

@app.post("/channels")
def create_channel(profile: ChannelProfile):
    data = profile.model_dump(by_alias=True)
    if not data.get("_id"):
        data["_id"] = str(uuid.uuid4())[:8]
    db.channels.update_one({"_id": data["_id"]}, {"$set": data}, upsert=True)
    return data

@app.get("/channels/{channel_id}")
def get_channel(channel_id: str):
    ch = db.channels.find_one({"_id": channel_id})
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ch

# --- Jobs API ---
@app.get("/jobs")
def list_jobs():
    return list(db.jobs.find())

@app.post("/jobs")
def create_job(body: dict):
    channel_id = body.get("channel_id", "default")
    autonomy = body.get("autonomy", settings.AUTONOMY_LEVEL)
    custom_topic = body.get("topic")
    custom_content = body.get("content") or body.get("script_text")
    story_style = body.get("story_style", "cartoon_story")
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    
    job_record = {
        "_id": job_id,
        "channel_id": channel_id,
        "autonomy": autonomy,
        "custom_topic": custom_topic,
        "custom_content": custom_content,
        "story_style": story_style,
        "status": "queued",
        "current_node": "pending"
    }
    db.jobs.insert_one(job_record)
    
    # Run pipeline asynchronously
    run_job_async(job_id, channel_id, autonomy, custom_topic=custom_topic, custom_content=custom_content, story_style=story_style)
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job_record = db.jobs.find_one({"_id": job_id})
    if not job_record:
        raise HTTPException(status_code=404, detail="Job not found")
        
    cfg = {"configurable": {"thread_id": job_id}}
    try:
        snap = app_graph.get_state(cfg)
        return {
            "job_id": job_id,
            "status": job_record.get("status", "running"),
            "current_node": job_record.get("current_node", ""),
            "next": list(snap.next) if snap else [],
            "values": snap.values if snap else {}
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": job_record.get("status", "pending"),
            "current_node": job_record.get("current_node", ""),
            "next": [],
            "values": {}
        }

@app.post("/jobs/{job_id}/resume")
def resume_job_route(job_id: str, decision: dict):
    """
    Submit human review decision:
    {'action': 'approve'} or {'action': 'edit', 'script': {...}} or {'action': 'reject'}
    """
    from app.worker import resume_job_async
    resume_job_async(job_id, decision)
    return {"ok": True, "resumed_job": job_id, "decision": decision}

# --- Kill Switch & Operations ---
@app.post("/kill-switch")
def kill_switch(body: dict):
    is_on = bool(body.get("on", False))
    db.settings.update_one({"_id": "kill_switch"}, {"$set": {"on": is_on}}, upsert=True)
    return {"kill_switch_active": is_on}

@app.get("/kill-switch")
def get_kill_switch():
    setting = db.settings.find_one({"_id": "kill_switch"})
    return {"kill_switch_active": bool(setting.get("on", False)) if setting else False}

# --- Calendar & Publishing ---
@app.get("/calendar")
def get_calendar():
    return {
        "scheduled_slots": [
            {"slot": "2026-10-27T18:00:00Z", "channel": "default", "status": "reserved"},
            {"slot": "2026-10-30T18:00:00Z", "channel": "default", "status": "open"}
        ]
    }

# --- YouTube Shorts Generator (Blueprint 2 & 12) ---
@app.post("/jobs/{job_id}/shorts")
def create_shorts_route(job_id: str):
    from app.shorts import generate_shorts_from_job
    job_rec = db.jobs.find_one({"_id": job_id})
    if not job_rec:
        raise HTTPException(status_code=404, detail="Job not found")
        
    cfg = {"configurable": {"thread_id": job_id}}
    snap = app_graph.get_state(cfg)
    state = snap.values if snap else {}
    if not state.get("script"):
        raise HTTPException(status_code=400, detail="Job has not generated a script yet.")

    short_result = generate_shorts_from_job(state, short_idx=1)
    db.renders.insert_one({"job_id": job_id, "type": "short_9_16", **short_result})
    return short_result

# --- Multilingual Fan-Out (Blueprint 21.10) ---
@app.post("/jobs/{job_id}/fanout")
def fanout_route(job_id: str, body: dict):
    from app.fanout import fanout_multilingual_jobs
    target_channels = body.get("target_channels", [])
    if not target_channels:
        raise HTTPException(status_code=400, detail="target_channels list required.")
    child_ids = fanout_multilingual_jobs(job_id, target_channels)
    return {"parent_job_id": job_id, "child_jobs": child_ids}

# --- Competitor Outlier Scout (Blueprint 8 & 14) ---
@app.get("/channels/{channel_id}/competitors")
def competitor_scout_route(channel_id: str):
    from app.competitor import run_competitor_outlier_study
    outliers = run_competitor_outlier_study(channel_id)
    return {"channel_id": channel_id, "outliers": outliers}

# --- Monetization & Affiliate Kit (Blueprint 13) ---
@app.get("/jobs/{job_id}/monetization")
def monetization_route(job_id: str):
    from app.monetization import generate_monetization_package
    job_rec = db.jobs.find_one({"_id": job_id})
    cfg = {"configurable": {"thread_id": job_id}}
    snap = app_graph.get_state(cfg)
    topic_data = snap.values.get("topic", {}) if snap else {}
    return generate_monetization_package(
        job_id,
        topic=topic_data.get("topic", "AI Infrastructure"),
        thesis=topic_data.get("thesis", "Transformer backlogs limit AI scale")
    )

# --- High-CTR Thumbnail Templates (Blueprint 6.10) ---
@app.post("/jobs/{job_id}/thumbnails")
def generate_thumbnails_route(job_id: str, body: dict = None):
    from app.thumbnail import generate_youtube_thumbnail
    body = body or {}
    text = body.get("headline", "THE 4-YEAR CHOKE")
    work = os.path.join(settings.STORAGE_DIR, job_id)
    os.makedirs(work, exist_ok=True)
    
    thumbs = []
    for t_idx in (1, 2, 3):
        out_file = os.path.join(work, f"thumb_variant_{t_idx}.png")
        generate_youtube_thumbnail(text, out_file, template_type=t_idx)
        thumbs.append({
            "template_id": t_idx,
            "url": f"/media/{job_id}/thumb_variant_{t_idx}.png",
            "path": out_file
        })
    return {"job_id": job_id, "variants": thumbs}

# --- Real-Time WebSocket for Live Progress Updates ---
@app.websocket("/ws/jobs/{job_id}")
async def job_websocket(sock: WebSocket, job_id: str):
    await sock.accept()
    last_node = None
    try:
        while True:
            cfg = {"configurable": {"thread_id": job_id}}
            job_rec = db.jobs.find_one({"_id": job_id})
            curr_node = job_rec.get("current_node") if job_rec else None
            
            if curr_node != last_node:
                await sock.send_json({
                    "job_id": job_id,
                    "node": curr_node,
                    "status": job_rec.get("status", "running") if job_rec else "unknown"
                })
                last_node = curr_node
                
            if job_rec and job_rec.get("status") in ("completed", "failed"):
                await sock.send_json({
                    "job_id": job_id,
                    "node": curr_node,
                    "status": job_rec.get("status")
                })
                break
                
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from WebSocket for job {job_id}")
