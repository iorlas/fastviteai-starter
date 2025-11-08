import pytest

from dagster_project.core.aggregator_resolver import resolve_url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_handles_regular_urls():
    result = await resolve_url("https://example.com/article")

    assert result.resolved_url == "https://example.com/article"
    assert len(result.discussion_links) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_resolves_hackernews():
    result = await resolve_url("https://news.ycombinator.com/item?id=45762012")

    assert len(result.discussion_links) == 1
    assert result.discussion_links[0].type == "hackernews"
    assert result.resolved_url is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_extracts_hn_external_links():
    result = await resolve_url("https://news.ycombinator.com/item?id=1")

    assert len(result.discussion_links) == 1
    assert result.discussion_links[0].type == "hackernews"
    assert result.resolved_url is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_resolves_lobsters():
    result = await resolve_url("https://lobste.rs/s/7w2aj3")

    assert result.resolved_url is not None
    assert len(result.discussion_links) == 1
    assert result.discussion_links[0].type == "lobsters"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_extracts_lobsters_external_links():
    result = await resolve_url("https://lobste.rs/s/7w2aj3")

    assert result.resolved_url is not None
    assert len(result.discussion_links) == 1
    assert result.discussion_links[0].url.startswith("https://lobste.rs")
