import threading
import logging
from app.config import settings
from app.db import db
from app.graph import app_graph

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    celery = Celery('studio', broker=settings.REDIS_URL)
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=True,
    )
except ImportError:
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(fn):
                def wrapper(*a, **kw):
                    return fn(*a, **kw)
                wrapper.delay = lambda *a, **kw: threading.Thread(target=fn, args=a, kwargs=kw, daemon=True).start()
                return wrapper
            return decorator
    celery = DummyCelery()

def execute_pipeline(job_id: str, channel_id: str, autonomy: int = 1, custom_topic: str = None, custom_content: str = None, story_style: str = "cartoon_story"):
    """Core execution logic for a video generation job."""
    try:
        db.jobs.update_one({'_id': job_id}, {'$set': {'status': 'running', 'current_node': 'strategist'}})
        cfg = {"configurable": {"thread_id": job_id}}
        initial_state = {
            "job_id": job_id,
            "channel_id": channel_id,
            "autonomy": autonomy,
            "rewrite_count": 0,
            "custom_topic": custom_topic,
            "custom_content": custom_content,
            "story_style": story_style
        }
        
        # Stream / run nodes
        for event in app_graph.stream(initial_state, cfg, stream_mode="updates"):
            for node_name, state_update in event.items():
                logger.info(f"[Job {job_id}] Node completed: {node_name}")
                db.jobs.update_one({'_id': job_id}, {'$set': {'current_node': node_name, 'last_update': node_name}})
        
        db.jobs.update_one({'_id': job_id}, {'$set': {'status': 'completed'}})
    except Exception as e:
        logger.error(f"[Job {job_id}] Error in pipeline: {e}", exc_info=True)
        db.jobs.update_one({'_id': job_id}, {'$set': {'status': 'failed', 'error': str(e)}})

@celery.task(bind=True, max_retries=1)
def run_job(self, job_id: str, channel_id: str, autonomy: int = 1, custom_topic: str = None, custom_content: str = None, story_style: str = "cartoon_story"):
    execute_pipeline(job_id, channel_id, autonomy, custom_topic, custom_content, story_style)

def resume_job(job_id: str, decision: dict):
    cfg = {"configurable": {"thread_id": job_id}}
    try:
        logger.info(f"Resuming job {job_id} with human decision: {decision}")
        if decision.get("action") == "edit" and "script" in decision:
            db.scripts.update_one({"job_id": job_id}, {"$set": {"script": decision["script"]}}, upsert=True)
            
        for event in app_graph.stream({"qa": {"human": decision}}, cfg, stream_mode="updates"):
            for node_name, state_update in event.items():
                logger.info(f"[Job {job_id}] Node completed: {node_name}")
                db.jobs.update_one({'_id': job_id}, {'$set': {'current_node': node_name, 'last_update': node_name}})
        db.jobs.update_one({'_id': job_id}, {'$set': {'status': 'completed'}})
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}", exc_info=True)

def resume_job_async(job_id: str, decision: dict):
    """Spawns resume execution in background thread for local dev mode."""
    t = threading.Thread(target=resume_job, args=(job_id, decision), daemon=True)
    t.start()

def run_job_async(job_id: str, channel_id: str, autonomy: int = 1, custom_topic: str = None, custom_content: str = None, story_style: str = "cartoon_story"):
    """Spawns execution in background thread for local dev mode."""
    logger.info(f"Starting async background pipeline execution for job: {job_id}")
    t = threading.Thread(target=execute_pipeline, args=(job_id, channel_id, autonomy, custom_topic, custom_content, story_style), daemon=True)
    t.start()
