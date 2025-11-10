import pytest

from dagster_project.core.discussions.hn_client import HackerNewsClient
from dagster_project.utils.url_utils import normalize_url


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

        # Verify UnifiedDiscussion structure (BaseModel - use attribute access)
        assert story.id == str(story_id)
        assert story.platform == "hackernews"
        assert story.title
        assert story.author
        assert isinstance(story.points, int)
        assert isinstance(story.comments, list)
        assert story.discussion_url
        assert story.comment_count


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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_by_url_returns_only_exact_matches():
    """Test that search_by_url filters out child path URLs and returns only exact matches.

    Example: Searching for https://www.cs.utexas.edu/~EWD/ should NOT return
    stories for https://www.cs.utexas.edu/~EWD/transcriptions/EWD06xx/EWD667.html
    """
    async with HackerNewsClient() as client:
        # Known URL with child paths posted to HN
        base_url = "https://www.cs.utexas.edu/~EWD/"
        discussion_urls = await client.search_by_url(base_url)

        # Verify each returned story has an exact URL match (normalized)
        normalized_base = normalize_url(base_url)

        for disc_url in discussion_urls:
            story_id = client.extract_story_id(disc_url)
            story = await client.fetch_story_with_comments(story_id)

            # Story URL should match exactly (after normalization)
            if story.article_url:
                normalized_story_url = normalize_url(story.article_url)
                assert normalized_story_url == normalized_base, (
                    f"Expected exact match for {base_url}, but got {story.article_url} (story ID: {story_id})"
                )
