import os
import httpx
import logging
from app.db import db
from app.tools import cached

logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def search_stock_video(query: str, orientation: str = "landscape") -> dict | None:
    """
    Search Pexels API for free stock footage with commercial license
    matching Blueprint Section 6.7.
    """
    if not PEXELS_API_KEY:
        return None

    def _call():
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation={orientation}"
        try:
            resp = httpx.get(url, headers=headers, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                videos = data.get("videos", [])
                if videos:
                    best_video = videos[0]
                    # Select 1080p or highest available mp4 file
                    files = best_video.get("video_files", [])
                    mp4s = [f for f in files if f.get("file_type") == "video/mp4"]
                    mp4s.sort(key=lambda x: x.get("width", 0), reverse=True)
                    if mp4s:
                        return {
                            "download_url": mp4s[0]["link"],
                            "license": "Pexels Free to Use",
                            "attribution": f"Video by {best_video.get('user', {}).get('name', 'Pexels Creator')} on Pexels",
                            "duration": best_video.get("duration", 5)
                        }
        except Exception as e:
            logger.warning(f"Pexels stock video search failed: {e}")
        return None

    return cached(f"pexels:vid:{query}:{orientation}", 86400 * 7, _call)

def download_asset(url: str, dest_path: str, license_info: dict, job_id: str):
    """Download stock media asset and record license metadata into MongoDB."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with httpx.stream("GET", url, timeout=30.0) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    # Save attribution & license compliance record (Blueprint Section 8)
    db.research_notes.insert_one({
        "job_id": job_id,
        "type": "media_license",
        "asset_path": dest_path,
        "license": license_info.get("license", "Public / Licensed"),
        "attribution": license_info.get("attribution", "")
    })
    return dest_path
