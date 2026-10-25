import os
import time
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from app.db import redis_client
from app.config import settings

logger = logging.getLogger(__name__)

# Daily quota limit tracker (Blueprint Section 11 & 20)
DAILY_QUOTA_LIMIT = 10000  # Default YouTube Data API v3 daily quota limit
UPLOAD_COST = 1600         # Videos.insert quota cost

def guard_quota(cost_units: int = UPLOAD_COST):
    """Guard against exceeding daily YouTube API quota using Redis counter."""
    key = f"yt_quota:{time.strftime('%Y-%m-%d')}"
    try:
        used = redis_client.get(key)
        used_int = int(used) if used else 0
        if used_int + cost_units > DAILY_QUOTA_LIMIT:
            raise RuntimeError(f"YouTube daily API quota budget reached: {used_int}/{DAILY_QUOTA_LIMIT} units. Publishing blocked.")
        redis_client.setex(key, 86400, used_int + cost_units)
    except Exception as e:
        logger.warning(f"Quota check skipped or Redis unavailable: {e}")

def upload_video_to_youtube(creds, video_path: str, meta: dict, publish_at: str = None) -> str:
    """
    Resumable scheduled upload to YouTube with thumbnail and synthetic media flag
    matching Blueprint Section 11 and 19.
    """
    guard_quota(UPLOAD_COST)
    yt = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': meta.get('title', 'Explainer Video')[:60],
            'description': meta.get('description', ''),
            'tags': meta.get('tags', []),
            'categoryId': '27',  # Education / Science & Tech
            'defaultLanguage': meta.get('default_language', 'en'),
            'defaultAudioLanguage': meta.get('default_language', 'en'),
        },
        'status': {
            'privacyStatus': 'private',  # Stays private until scheduled publishAt
            'selfDeclaredMadeForKids': False,
            # AI disclosure flag (Blueprint Section 11 & 20)
            'containsSyntheticMedia': True,
        }
    }

    if publish_at:
        body['status']['publishAt'] = publish_at  # RFC 3339 UTC string

    media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part='snippet,status', body=body, media_body=media)

    resp = None
    tries = 0
    while resp is None:
        try:
            status, resp = req.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}% to YouTube...")
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and tries < 5:
                tries += 1
                time.sleep(2 ** tries)
            else:
                raise

    vid = resp['id']
    logger.info(f"Video uploaded successfully. Video ID: {vid}")

    # Set custom thumbnail if available
    thumb_path = meta.get('thumb')
    if thumb_path and os.path.exists(thumb_path):
        try:
            yt.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(thumb_path)
            ).execute()
            logger.info("Custom thumbnail set.")
        except Exception as e:
            logger.warning(f"Failed to set custom thumbnail: {e}")

    return vid
