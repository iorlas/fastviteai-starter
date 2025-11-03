import pytest

from dagster_project.core.discussions.hn_client import HNClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_by_url_finds_stories():
    async with HNClient() as client:
        url = "https://blog.samaltman.com/what-i-wish-someone-had-told-me"
        stories = await client.search_by_url(url)

        assert isinstance(stories, list)
        if stories:
            assert stories[0].url is not None
            assert stories[0].story_id > 0
            assert stories[0].title
            assert stories[0].author


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_story_with_comments():
    async with HNClient() as client:
        story_id = 8863
        story = await client.fetch_story_with_comments(story_id)

        assert story.story_id == story_id
        assert story.title
        assert isinstance(story.children, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_no_results():
    async with HNClient() as client:
        url = "https://nonexistent-domain-12345.com/article"
        stories = await client.search_by_url(url)

        assert isinstance(stories, list)
        assert len(stories) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_client_context_manager():
    async with HNClient(timeout=10) as client:
        assert client.client is not None
        assert client.timeout == 10
