import tempfile
from pathlib import Path

import pytest

from dagster_project.core.cache.hishel_cache import get_async_cache_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_cache_miss_and_fetch():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        client = get_async_cache_client(cache_dir=cache_dir)

        response1 = await client.get("https://example.com")
        assert response1.status_code == 200
        assert "Example Domain" in response1.text
        assert response1.extensions.get("hishel_from_cache") is False

        response2 = await client.get("https://example.com")
        assert response2.status_code == 200
        assert "Example Domain" in response2.text
        assert response2.extensions.get("hishel_from_cache") is True

        assert response1.text == response2.text
        await client.aclose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_cache_stores_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        client = get_async_cache_client(cache_dir=cache_dir, ttl=3600)

        response = await client.get("https://example.com")

        assert response.status_code == 200
        assert str(response.url).startswith("https://example.com")
        assert "text/html" in response.headers.get("content-type", "").lower()
        await client.aclose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_cache_reuses_cached_response():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        client = get_async_cache_client(cache_dir=cache_dir)

        response1 = await client.get("https://example.com")
        html1 = response1.text

        response2 = await client.get("https://example.com")
        html2 = response2.text

        assert html1 == html2
        assert response2.extensions.get("hishel_from_cache") is True
        await client.aclose()
