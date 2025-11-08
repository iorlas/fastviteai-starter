import pytest

from dagster_project.core.aggregator_resolver import resolve_url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_handles_regular_urls():
    resolved_url, discussion_link = await resolve_url("https://example.com/article")

    assert resolved_url == "https://example.com/article"
    assert discussion_link is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_resolves_hackernews():
    resolved_url, discussion_link = await resolve_url("https://news.ycombinator.com/item?id=45762012")

    assert discussion_link is not None
    assert discussion_link.type == "hackernews"
    assert resolved_url is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_extracts_hn_external_links():
    resolved_url, discussion_link = await resolve_url("https://news.ycombinator.com/item?id=1")

    assert discussion_link is not None
    assert discussion_link.type == "hackernews"
    assert resolved_url is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_resolves_lobsters():
    resolved_url, discussion_link = await resolve_url("https://lobste.rs/s/7w2aj3")

    assert resolved_url is not None
    assert discussion_link is not None
    assert discussion_link.type == "lobsters"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_url_extracts_lobsters_external_links():
    resolved_url, discussion_link = await resolve_url("https://lobste.rs/s/7w2aj3")

    assert resolved_url is not None
    assert discussion_link is not None
    assert discussion_link.url.startswith("https://lobste.rs")
