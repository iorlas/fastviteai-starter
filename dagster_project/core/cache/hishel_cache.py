from pathlib import Path

import structlog
from hishel import AsyncSqliteStorage, CacheOptions, SpecificationPolicy
from hishel.httpx import AsyncCacheClient

logger = structlog.get_logger()

DEFAULT_CACHE_DIR = Path("artifacts/cache/http_responses")
DEFAULT_TTL = 3600  # 1 hour


def get_async_cache_client(
    cache_dir: Path | None = None,
    ttl: int = DEFAULT_TTL,
    timeout: int = 30,
) -> AsyncCacheClient:
    """Get configured async cache client with caching enabled.

    Caches ALL responses for the specified TTL using Hishel with SQLite storage.
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    cache_dir.mkdir(parents=True, exist_ok=True)

    storage = AsyncSqliteStorage(
        database_path=str(cache_dir / "http_cache.db"),
        default_ttl=float(ttl),
        refresh_ttl_on_access=False,
    )

    cache_options = CacheOptions(allow_stale=True)
    policy = SpecificationPolicy(cache_options=cache_options)

    return AsyncCacheClient(
        storage=storage,
        policy=policy,
        timeout=timeout,
        follow_redirects=True,
    )
