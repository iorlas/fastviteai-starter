from datetime import datetime, timedelta
from pathlib import Path

import httpx
import structlog
from pydantic import BaseModel

from dagster_project.core.cache.cache_store import CacheStore

logger = structlog.get_logger()


class CachedHTTPResponse(BaseModel):
    url: str
    response_text: str
    status_code: int
    headers: dict[str, str]
    timestamp: str
    ttl_seconds: int | None


class HTTPCache:
    def __init__(self, cache_dir: Path | None = None):
        if cache_dir is None:
            cache_dir = Path("artifacts/cache/http_responses")
        self.store = CacheStore(cache_dir)

    def _is_expired(self, cached: CachedHTTPResponse) -> bool:
        if cached.ttl_seconds is None:
            return False

        cached_time = datetime.fromisoformat(cached.timestamp)
        expiry_time = cached_time + timedelta(seconds=cached.ttl_seconds)
        return datetime.now() > expiry_time

    def get(self, url: str) -> CachedHTTPResponse | None:
        cached_data = self.store.get(url)

        if cached_data is None:
            logger.debug("cache_miss", url=url)
            return None

        try:
            cached = CachedHTTPResponse(**cached_data)

            if self._is_expired(cached):
                logger.debug("cache_expired", url=url)
                self.store.delete(url)
                return None

            logger.debug("cache_hit", url=url)
            return cached

        except Exception as e:
            logger.warning("cache_invalid", url=url, error=str(e))
            return None

    def set(self, url: str, response: httpx.Response, ttl_seconds: int | None = None) -> None:
        cached = CachedHTTPResponse(
            url=url,
            response_text=response.text,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items()},
            timestamp=datetime.now().isoformat(),
            ttl_seconds=ttl_seconds,
        )

        self.store.set(url, cached.model_dump())
        logger.debug("http_cached", url=url, ttl=ttl_seconds)

    def fetch(self, url: str, ttl_seconds: int | None = None, timeout: int = 15) -> str:
        cached = self.get(url)

        if cached is not None:
            return cached.response_text

        logger.info("http_fetch", url=url)

        try:
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()

            self.set(url, response, ttl_seconds=ttl_seconds)

            return response.text

        except Exception as e:
            logger.error("http_fetch_failed", url=url, error=str(e))
            raise
