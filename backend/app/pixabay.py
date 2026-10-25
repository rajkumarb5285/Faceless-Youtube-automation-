import os
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

def clean_search_term(query: str) -> str:
    """Simplify verbose prompt descriptions to clean keywords for stock search."""
    clean = query.replace("illustration of", "").replace("cartoon of", "").replace("photo of", "").replace("4k", "").strip()
    words = [w for w in clean.split() if len(w) > 3][:3]
    return " ".join(words) if words else clean

def search_pixabay_videos(query: str, limit: int = 3) -> list[dict]:
    """Search Pixabay for high-definition stock video clips (MP4)."""
    if not settings.PIXABAY_API_KEY:
        logger.warning("PIXABAY_API_KEY not configured.")
        return []

    term = clean_search_term(query)
    try:
        url = "https://pixabay.com/api/videos/"
        params = {
            "key": settings.PIXABAY_API_KEY,
            "q": term,
            "per_page": max(3, limit)
        }
        resp = httpx.get(url, params=params, timeout=12.0)
        if resp.status_code != 200:
            logger.warning(f"Pixabay video search error ({resp.status_code}): {resp.text[:100]}")
            return []

        hits = resp.json().get("hits", [])
        results = []
        for h in hits:
            v_dict = h.get("videos", {})
            # Prefer 1080p (large) or 720p (medium)
            mp4_url = (v_dict.get("large", {}).get("url") or 
                       v_dict.get("medium", {}).get("url") or 
                       v_dict.get("small", {}).get("url"))
            if mp4_url:
                results.append({
                    "id": h.get("id"),
                    "tags": h.get("tags", ""),
                    "duration": h.get("duration", 10),
                    "url": mp4_url
                })
        return results
    except Exception as e:
        logger.warning(f"Pixabay video search exception for '{term}': {e}")
        return []

def download_pixabay_video(query: str, out_path: str) -> Optional[str]:
    """Download best matching Pixabay HD stock video clip."""
    if not settings.PIXABAY_API_KEY:
        return None

    videos = search_pixabay_videos(query, limit=3)
    if not videos:
        # Fallback to broader technology/nature theme
        videos = search_pixabay_videos("technology", limit=3)
        if not videos:
            return None

    download_url = videos[0]["url"]
    try:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with httpx.stream("GET", download_url, timeout=25.0) as resp:
            if resp.status_code != 200:
                return None
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            logger.info(f"Downloaded Pixabay stock video ({os.path.getsize(out_path)} bytes) for '{query}' to {out_path}")
            return out_path
    except Exception as e:
        logger.warning(f"Pixabay video download failed: {e}")

    return None

def search_pixabay_images(query: str, limit: int = 3) -> list[str]:
    """Search Pixabay for high-resolution stock images/illustrations."""
    if not settings.PIXABAY_API_KEY:
        return []

    term = clean_search_term(query)
    try:
        url = "https://pixabay.com/api/"
        params = {
            "key": settings.PIXABAY_API_KEY,
            "q": term,
            "per_page": max(3, limit),
            "safesearch": "true"
        }
        resp = httpx.get(url, params=params, timeout=12.0)
        if resp.status_code != 200:
            return []

        hits = resp.json().get("hits", [])
        urls = []
        for h in hits:
            img_url = h.get("largeImageURL") or h.get("webformatURL")
            if img_url:
                urls.append(img_url)
        return urls
    except Exception as e:
        logger.warning(f"Pixabay image search error for '{term}': {e}")
        return []

def download_pixabay_image(query: str, out_path: str) -> Optional[str]:
    """Download matching Pixabay image."""
    images = search_pixabay_images(query, limit=3)
    if not images:
        return None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        resp = httpx.get(images[0], timeout=15.0)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"Downloaded Pixabay image for '{query}' ({len(resp.content)} bytes)")
            return out_path
    except Exception as e:
        logger.warning(f"Pixabay image download error: {e}")

    return None
