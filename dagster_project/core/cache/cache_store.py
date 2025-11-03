import hashlib
import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class CacheStore:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("cache_read_failed", key=key, error=str(e))
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "w") as f:
                json.dump(value, f, indent=2)
            logger.debug("cache_write_success", key=key)
        except Exception as e:
            logger.error("cache_write_failed", key=key, error=str(e))
            raise

    def exists(self, key: str) -> bool:
        return self._get_cache_path(key).exists()

    def delete(self, key: str) -> None:
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug("cache_delete_success", key=key)
