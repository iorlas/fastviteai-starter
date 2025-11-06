import pytest

from dagster_project.core.aggregators.hackernews import HackerNewsExtractor


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_extracts_article_url():
    extractor = HackerNewsExtractor()

    result = await extractor.extract_article_url("https://news.ycombinator.com/item?id=45762012")

    assert result.article_url is not None
    assert result.article_url != "https://news.ycombinator.com/item?id=45762012"
    assert result.title is not None
    assert len(result.title) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_handles_external_links():
    extractor = HackerNewsExtractor()

    result = await extractor.extract_article_url("https://news.ycombinator.com/item?id=1")

    assert result.article_url is not None
    assert result.title is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hn_extractor_raises_on_invalid_url():
    extractor = HackerNewsExtractor()

    with pytest.raises(Exception):
        await extractor.extract_article_url("https://news.ycombinator.com/invalid")
