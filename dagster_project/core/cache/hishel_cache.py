from pathlib import Path

import structlog
from hishel import AsyncSqliteStorage, FilterPolicy
from hishel._policies import BaseFilter, Response
from hishel.httpx import AsyncCacheClient

logger = structlog.get_logger()

DEFAULT_CACHE_DIR = Path("artifacts/cache/http_responses")
DEFAULT_TTL = 3600  # 1 hour


class StatusCodeFilter(BaseFilter[Response]):
    """Filter that prevents caching of 403 and 5xx error responses."""

    def needs_body(self) -> bool:
        return False

    def apply(self, response: Response, body: bytes | None) -> bool:
        """Return True if response should be cached, False otherwise."""
        status_code = response.status_code
        # Only cache successful responses (2xx) and redirects (301, 308)
        # Explicitly reject 403 and 5xx errors
        if status_code == 403 or (status_code >= 500 and status_code < 600):
            return False
        # Cache 2xx and permanent redirects
        return 200 <= status_code < 300 or status_code in (301, 308)


def get_async_cache_client(
    cache_dir: Path | None = None,
    ttl: int = DEFAULT_TTL,
    timeout: int = 30,
) -> AsyncCacheClient:
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    cache_dir.mkdir(parents=True, exist_ok=True)

    storage = AsyncSqliteStorage(
        database_path=str(cache_dir / "http_cache.db"),
        default_ttl=float(ttl),
        refresh_ttl_on_access=False,
    )

    status_filter = StatusCodeFilter()
    policy = FilterPolicy(response_filters=[status_filter])

    return AsyncCacheClient(
        storage=storage,
        policy=policy,
        timeout=timeout,
        follow_redirects=True,
    )
