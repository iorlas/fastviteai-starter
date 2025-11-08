import pytest

from dagster_project.core.discussions.hn_client import HackerNewsClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_extracts_article_url():
    async with HackerNewsClient() as client:
        result = await client.extract_article_url("https://news.ycombinator.com/item?id=45762012")

    assert result.article_url is not None
    assert result.article_url != "https://news.ycombinator.com/item?id=45762012"
    assert result.title is not None
    assert len(result.title) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_handles_external_links():
    async with HackerNewsClient() as client:
        result = await client.extract_article_url("https://news.ycombinator.com/item?id=1")

        assert result.article_url is not None
        assert result.title is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_raises_on_invalid_url():
    async with HackerNewsClient() as client:
        with pytest.raises(Exception):
            await client.extract_article_url("https://news.ycombinator.com/invalid")
