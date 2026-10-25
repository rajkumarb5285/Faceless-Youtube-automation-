import uuid
import logging
from app.db import db
from app.worker import run_job_async

logger = logging.getLogger(__name__)

def fanout_multilingual_jobs(parent_job_id: str, target_channel_ids: list[str]) -> list[str]:
    """
    Multi-language Fan-Out (Blueprint Section 21.10).
    Reuses the single verified research dossier & claims table from the parent job,
    spawning dedicated child jobs for target languages (e.g. Hindi, Tamil, English).
    Each child job produces a native script, voice, and render tailored to its target audience.
    """
    parent_job = db.jobs.find_one({"_id": parent_job_id})
    if not parent_job:
        raise ValueError(f"Parent job {parent_job_id} not found.")

    parent_claims = db.claims.find_one({"job_id": parent_job_id})
    parent_research = db.research_notes.find({"job_id": parent_job_id})

    child_job_ids = []
    for chan_id in target_channel_ids:
        child_id = f"lang_{chan_id}_{uuid.uuid4().hex[:6]}"
        
        # Create child job record linked to parent claims
        child_job = {
            "_id": child_id,
            "parent_job_id": parent_job_id,
            "channel_id": chan_id,
            "autonomy": parent_job.get("autonomy", 1),
            "status": "queued",
            "current_node": "planner",
            "is_multilingual_child": True
        }
        db.jobs.insert_one(child_job)

        # Attach parent verified claims to child
        if parent_claims:
            db.claims.insert_one({
                "job_id": child_id,
                "claims": parent_claims.get("claims", [])
            })

        logger.info(f"Spawned multilingual child job: {child_id} for channel {chan_id}")
        run_job_async(child_id, chan_id, parent_job.get("autonomy", 1))
        child_job_ids.append(child_id)

    return child_job_ids
