import os
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

def search_coverr_videos(query: str, limit: int = 5) -> list[dict]:
    """
    Search Coverr for high-quality royalty-free cinematic stock video clips.
    """
    if not settings.COVERR_API_KEY:
        logger.warning("COVERR_API_KEY not configured.")
        return []

    try:
        url = "https://api.coverr.co/videos"
        headers = {
            "Authorization": f"Bearer {settings.COVERR_API_KEY}"
        }
        params = {
            "query": query,
            "page_size": limit
        }
        resp = httpx.get(url, params=params, headers=headers, timeout=12.0)
        if resp.status_code != 200:
            logger.warning(f"Coverr search failed ({resp.status_code}): {resp.text[:100]}")
            return []

        data = resp.json()
        hits = data.get("hits", [])
        results = []
        for h in hits:
            vid_id = h.get("id") or h.get("video_id")
            title = h.get("title", "")
            duration = float(h.get("duration", 10.0))
            thumb = h.get("thumbnail") or h.get("poster")
            results.append({
                "id": vid_id,
                "title": title,
                "duration": duration,
                "thumbnail": thumb
            })
        return results
    except Exception as e:
        logger.warning(f"Coverr video search error for '{query}': {e}")
        return []

def get_coverr_download_url(video_id: str) -> Optional[str]:
    """Fetch direct MP4 download link for a Coverr video."""
    if not settings.COVERR_API_KEY:
        return None

    try:
        url = f"https://api.coverr.co/videos/{video_id}"
        headers = {"Authorization": f"Bearer {settings.COVERR_API_KEY}"}
        resp = httpx.get(url, headers=headers, timeout=10.0)
        if resp.status_code != 200:
            return None
        detail = resp.json()

        # Check default_variant renditions first (720p or 1080p)
        renditions = detail.get("default_variant", {}).get("renditions", [])
        for r in renditions:
            if r.get("type") in ("hd", "fhd") and r.get("url"):
                return r["url"]

        urls = detail.get("urls", {})
        return urls.get("mp4") or urls.get("mp4_download") or urls.get("mp4_preview")
    except Exception as e:
        logger.warning(f"Error fetching Coverr detail for {video_id}: {e}")
        return None

def download_coverr_clip(query: str, out_path: str) -> Optional[str]:
    """
    Search Coverr for a query and download the MP4 stock clip to out_path.
    Returns out_path on success, or None on failure.
    """
    if not settings.COVERR_API_KEY:
        return None

    # Simplify query to main keyword nouns for better stock search recall
    clean_query = query.replace("illustration of", "").replace("cartoon of", "").replace("4k", "").strip()
    words = [w for w in clean_query.split() if len(w) > 3][:3]
    search_term = " ".join(words) if words else clean_query

    hits = search_coverr_videos(search_term, limit=3)
    if not hits and search_term != clean_query:
        hits = search_coverr_videos(clean_query, limit=3)

    if not hits:
        # Fallback to broader themes
        hits = search_coverr_videos("technology", limit=1)
        if not hits:
            return None

    video_id = hits[0]["id"]
    download_url = get_coverr_download_url(video_id)
    if not download_url:
        return None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with httpx.stream("GET", download_url, timeout=25.0) as resp:
            if resp.status_code != 200:
                return None
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            logger.info(f"Downloaded Coverr stock video clip for '{search_term}' ({os.path.getsize(out_path)} bytes) to {out_path}")
            return out_path
    except Exception as e:
        logger.warning(f"Coverr video download failed: {e}")

    return None
