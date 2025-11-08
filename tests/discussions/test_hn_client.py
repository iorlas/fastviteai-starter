import pytest

from dagster_project.core.discussions.hn_client import HackerNewsClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_by_url_finds_stories():
    async with HackerNewsClient() as client:
        url = "https://blog.samaltman.com/what-i-wish-someone-had-told-me"
        discussion_urls = await client.search_by_url(url)

        assert isinstance(discussion_urls, list)
        if discussion_urls:
            assert isinstance(discussion_urls[0], str)
            assert "news.ycombinator.com/item?id=" in discussion_urls[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_story_with_comments():
    async with HackerNewsClient() as client:
        story_id = 8863
        story = await client.fetch_story_with_comments(story_id)

        assert story.story_id == story_id
        assert story.title
        assert isinstance(story.children, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_no_results():
    async with HackerNewsClient() as client:
        url = "https://nonexistent-domain-12345.com/article"
        stories = await client.search_by_url(url)

        assert isinstance(stories, list)
        assert len(stories) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_client_context_manager():
    async with HackerNewsClient(timeout=10) as client:
        assert client.client is not None
        assert client.timeout == 10
