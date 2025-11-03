import tempfile
from pathlib import Path

import pytest

from dagster_project.core.cache.http_cache import HTTPCache


@pytest.mark.integration
def test_http_cache_miss_and_fetch():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTTPCache(cache_dir=Path(tmpdir))

        cached = cache.get("https://example.com")
        assert cached is None

        html = cache.fetch("https://example.com", ttl_seconds=None)
        assert "Example Domain" in html

        cached = cache.get("https://example.com")
        assert cached is not None
        assert "Example Domain" in cached.response_text


@pytest.mark.integration
def test_http_cache_stores_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTTPCache(cache_dir=Path(tmpdir))

        cache.fetch("https://example.com", ttl_seconds=3600)

        cached = cache.get("https://example.com")
        assert cached is not None
        assert cached.url == "https://example.com"
        assert cached.status_code == 200
        assert cached.ttl_seconds == 3600
        assert "text/html" in cached.headers.get("content-type", "").lower()


@pytest.mark.integration
def test_http_cache_reuses_cached_response():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTTPCache(cache_dir=Path(tmpdir))

        html1 = cache.fetch("https://example.com", ttl_seconds=None)
        html2 = cache.fetch("https://example.com", ttl_seconds=None)

        assert html1 == html2
