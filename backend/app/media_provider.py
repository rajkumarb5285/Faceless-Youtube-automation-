import os
import time
import hashlib
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class MediaAsset:
    def __init__(
        self,
        file_path: str,
        provider: str,
        asset_type: str,  # 'video' or 'image'
        query: str,
        duration: float = 5.0,
        width: int = 1920,
        height: int = 1080,
        source_url: str = "",
        license_name: str = "Royalty-Free Stock License",
        attribution: str = ""
    ):
        self.file_path = file_path
        self.provider = provider
        self.asset_type = asset_type
        self.query = query
        self.duration = duration
        self.width = width
        self.height = height
        self.source_url = source_url
        self.license_name = license_name
        self.attribution = attribution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "provider": self.provider,
            "asset_type": self.asset_type,
            "query": self.query,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "source_url": self.source_url,
            "license_name": self.license_name,
            "attribution": self.attribution
        }

class BaseMediaProvider(ABC):
    def __init__(self, name: str):
        self.name = name
        self.circuit_open_until = 0.0
        self.failure_count = 0

    def is_available(self) -> bool:
        return time.time() > self.circuit_open_until

    def trip_circuit_breaker(self, cooldown_seconds: float = 300.0, duration_seconds: Optional[float] = None):
        cd = duration_seconds if duration_seconds is not None else cooldown_seconds
        self.circuit_open_until = time.time() + cd
        self.failure_count += 1
        logger.warning(f"Circuit breaker tripped for {self.name}. Paused for {cd}s (failures: {self.failure_count}).")

    @abstractmethod
    def fetch_video(self, query: str, out_path: str) -> Optional[MediaAsset]:
        pass

    @abstractmethod
    def fetch_image(self, query: str, out_path: str) -> Optional[MediaAsset]:
        pass

class CoverrProvider(BaseMediaProvider):
    def __init__(self):
        super().__init__("Coverr")

    def fetch_video(self, query: str, out_path: str) -> Optional[MediaAsset]:
        if not settings.COVERR_API_KEY or not self.is_available():
            return None

        clean_term = " ".join([w for w in query.replace("illustration", "").replace("cartoon", "").split() if len(w) > 3][:3]) or query
        url = "https://api.coverr.co/videos"
        headers = {"Authorization": f"Bearer {settings.COVERR_API_KEY}"}

        try:
            resp = httpx.get(url, params={"query": clean_term, "page_size": 3}, headers=headers, timeout=12.0)
            if resp.status_code == 403 or resp.status_code == 429:
                self.trip_circuit_breaker(300.0)
                return None
            if resp.status_code != 200:
                logger.warning(f"Coverr returned {resp.status_code} for '{clean_term}'")
                return None

            hits = resp.json().get("hits", [])
            if not hits:
                return None

            vid_id = hits[0].get("id") or hits[0].get("video_id")
            detail_resp = httpx.get(f"https://api.coverr.co/videos/{vid_id}", headers=headers, timeout=10.0)
            if detail_resp.status_code != 200:
                return None

            detail = detail_resp.json()
            dl_url = None
            for r in detail.get("default_variant", {}).get("renditions", []):
                if r.get("type") in ("fhd", "hd") and r.get("url"):
                    dl_url = r["url"]
                    break
            if not dl_url:
                dl_url = detail.get("urls", {}).get("mp4") or detail.get("urls", {}).get("mp4_download")

            if not dl_url:
                return None

            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with httpx.stream("GET", dl_url, timeout=25.0) as dl:
                if dl.status_code == 200:
                    with open(out_path, "wb") as f:
                        for chunk in dl.iter_bytes(65536):
                            f.write(chunk)

            if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
                return MediaAsset(
                    file_path=out_path,
                    provider="Coverr",
                    asset_type="video",
                    query=clean_term,
                    duration=float(hits[0].get("duration", 8.0)),
                    source_url=dl_url,
                    attribution=hits[0].get("title", "Coverr Free Stock Video")
                )
        except Exception as e:
            logger.warning(f"Coverr fetch exception: {e}")
        return None

    def fetch_image(self, query: str, out_path: str) -> Optional[MediaAsset]:
        return None  # Coverr is dedicated to stock video clips

class PixabayProvider(BaseMediaProvider):
    def __init__(self):
        super().__init__("Pixabay")

    def search_videos(self, query: str) -> List[Dict[str, Any]]:
        if not settings.PIXABAY_API_KEY or not self.is_available():
            return []
        try:
            url = "https://pixabay.com/api/videos/"
            params = {"key": settings.PIXABAY_API_KEY, "q": query, "per_page": 3}
            resp = httpx.get(url, params=params, timeout=10.0)
            if resp.status_code == 200:
                return resp.json().get("hits", [])
        except Exception:
            pass
        return []

    def fetch_video(self, query: str, out_path: str) -> Optional[MediaAsset]:
        if not settings.PIXABAY_API_KEY or not self.is_available():
            return None

        clean_term = " ".join([w for w in query.replace("illustration", "").replace("cartoon", "").split() if len(w) > 3][:3]) or query
        url = "https://pixabay.com/api/videos/"
        params = {"key": settings.PIXABAY_API_KEY, "q": clean_term, "per_page": 3}

        try:
            resp = httpx.get(url, params=params, timeout=12.0)
            if resp.status_code == 429:
                self.trip_circuit_breaker(120.0)
                return None
            if resp.status_code != 200:
                return None

            hits = resp.json().get("hits", [])
            if not hits:
                return None

            v_dict = hits[0].get("videos", {})
            dl_url = v_dict.get("large", {}).get("url") or v_dict.get("medium", {}).get("url")
            if not dl_url:
                return None

            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with httpx.stream("GET", dl_url, timeout=25.0) as dl:
                if dl.status_code == 200:
                    with open(out_path, "wb") as f:
                        for chunk in dl.iter_bytes(65536):
                            f.write(chunk)

            if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
                return MediaAsset(
                    file_path=out_path,
                    provider="Pixabay",
                    asset_type="video",
                    query=clean_term,
                    duration=float(hits[0].get("duration", 6.0)),
                    source_url=dl_url,
                    attribution=f"Pixabay #{hits[0].get('id')}"
                )
        except Exception as e:
            logger.warning(f"Pixabay video fetch exception: {e}")
        return None

    def fetch_image(self, query: str, out_path: str) -> Optional[MediaAsset]:
        if not settings.PIXABAY_API_KEY or not self.is_available():
            return None

        clean_term = " ".join([w for w in query.split() if len(w) > 3][:3]) or query
        url = "https://pixabay.com/api/"
        params = {"key": settings.PIXABAY_API_KEY, "q": clean_term, "per_page": 3, "safesearch": "true"}

        try:
            resp = httpx.get(url, params=params, timeout=12.0)
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    img_url = hits[0].get("largeImageURL") or hits[0].get("webformatURL")
                    if img_url:
                        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                        img_bytes = httpx.get(img_url, timeout=15.0).content
                        if len(img_bytes) > 5000:
                            with open(out_path, "wb") as f:
                                f.write(img_bytes)
                            return MediaAsset(
                                file_path=out_path,
                                provider="Pixabay",
                                asset_type="image",
                                query=clean_term,
                                source_url=img_url,
                                attribution=f"Pixabay #{hits[0].get('id')}"
                            )
        except Exception as e:
            logger.warning(f"Pixabay image fetch exception: {e}")
        return None

class MediaProviderManager:
    """Orchestrates asset retrieval with deduplication, priority ladder, and caching."""
    def __init__(self):
        self.coverr = CoverrProvider()
        self.pixabay = PixabayProvider()
        self.providers: Dict[str, BaseMediaProvider] = {
            "coverr": self.coverr,
            "pixabay": self.pixabay
        }
        self.provider_list: List[BaseMediaProvider] = [self.coverr, self.pixabay]
        self._cache: Dict[str, Any] = {}

    def search_media(self, query: str, media_type: str = "video") -> List[Dict[str, Any]]:
        """Search media with deduplication across active providers."""
        norm_query = " ".join(query.lower().strip().split())
        cache_key = f"{norm_query}:{media_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        results = []
        for provider in self.provider_list:
            if provider.is_available():
                if hasattr(provider, "search_videos") and media_type == "video":
                    vids = provider.search_videos(norm_query)
                    if vids:
                        for v in vids:
                            results.append({**v, "provider": provider.name.lower()})
                        break
        self._cache[cache_key] = results
        return results

    def resolve_visual_asset(
        self,
        query: str,
        shot_id: str,
        work_dir: str,
        prefer_video: bool = True,
        palette: dict = None
    ) -> str:
        """Resolve highest-quality asset matching query with graceful fallbacks."""
        cache_key = f"{'vid' if prefer_video else 'img'}:{hashlib.md5(query.encode()).hexdigest()[:8]}"
        if cache_key in self._cache and os.path.exists(self._cache[cache_key]):
            return self._cache[cache_key]

        out_ext = "mp4" if prefer_video else "jpg"
        target_path = os.path.join(work_dir, f"asset_{shot_id}.{out_ext}")

        # 1. Try Video Providers
        if prefer_video:
            for provider in self.provider_list:
                if provider.is_available():
                    asset = provider.fetch_video(query, target_path)
                    if asset and os.path.exists(asset.file_path):
                        self._cache[cache_key] = asset.file_path
                        return asset.file_path

        # 2. Try Image Providers (e.g. Pixabay)
        target_img_path = os.path.join(work_dir, f"asset_{shot_id}.jpg")
        for provider in self.provider_list:
            if provider.is_available():
                asset = provider.fetch_image(query, target_img_path)
                if asset and os.path.exists(asset.file_path):
                    self._cache[cache_key] = asset.file_path
                    return asset.file_path

        # 3. Procedural Story Card Fallback
        from app.render import create_rich_cartoon_card
        card_path = os.path.join(work_dir, f"asset_card_{shot_id}.jpg")
        fallback_file = create_rich_cartoon_card(query, card_path, palette or {}, title="Visual Scene Beat")
        self._cache[cache_key] = fallback_file
        return fallback_file

media_manager = MediaProviderManager()
