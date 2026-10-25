import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

def search_viral_youtube_videos(query: str, max_results: int = 5) -> list[dict]:
    """
    Search top-performing viral YouTube videos in a niche using YouTube Data API v3.
    Returns title, videoId, views, likes, and tags for inspiration and outlier analysis.
    """
    if not settings.YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not configured.")
        return []

    try:
        # Step 1: Search videos ordered by viewCount
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "maxResults": max_results,
            "key": settings.YOUTUBE_API_KEY
        }
        resp = httpx.get(search_url, params=params, timeout=12.0)
        if resp.status_code != 200:
            logger.warning(f"YouTube search error ({resp.status_code}): {resp.text[:100]}")
            return []

        items = resp.json().get("items", [])
        if not items:
            return []

        video_ids = [it["id"]["videoId"] for it in items if "videoId" in it.get("id", {})]
        if not video_ids:
            return []

        # Step 2: Fetch video details & statistics
        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        v_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": settings.YOUTUBE_API_KEY
        }
        v_resp = httpx.get(videos_url, params=v_params, timeout=12.0)
        if v_resp.status_code != 200:
            return []

        v_items = v_resp.json().get("items", [])
        results = []
        for v in v_items:
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            results.append({
                "video_id": v["id"],
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "description": snippet.get("description", "")[:200],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "tags": snippet.get("tags", [])
            })
        return results
    except Exception as e:
        logger.warning(f"YouTube Data API scout error for '{query}': {e}")
        return []

def get_seo_tags_for_topic(topic: str) -> list[str]:
    """Extract winning SEO tags and keywords from top-ranking YouTube videos."""
    videos = search_viral_youtube_videos(topic, max_results=4)
    all_tags = []
    for v in videos:
        for t in v.get("tags", []):
            if t.lower() not in [x.lower() for x in all_tags]:
                all_tags.append(t)
    return all_tags[:15]
