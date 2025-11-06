import pytest

from dagster_project.core.discussions.lobsters_client import LobstersClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_by_url_finds_stories():
    async with LobstersClient() as client:
        url = "https://dave.cheney.net"
        story_urls = await client.search_by_url(url)

        assert isinstance(story_urls, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_story_with_comments():
    async with LobstersClient() as client:
        short_id = "7w2aj3"
        story = await client.fetch_story_with_comments(short_id)

        assert story.short_id == short_id
        assert story.title
        assert isinstance(story.comments, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_short_id_from_url():
    url = "https://lobste.rs/s/7w2aj3/some-title"
    short_id = LobstersClient.extract_short_id_from_url(url)

    assert short_id == "7w2aj3"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_short_id_invalid_url():
    url = "https://example.com/article"
    short_id = LobstersClient.extract_short_id_from_url(url)

    assert short_id is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_client_context_manager():
    async with LobstersClient(timeout=10) as client:
        assert client.client is not None
        assert client.timeout == 10
