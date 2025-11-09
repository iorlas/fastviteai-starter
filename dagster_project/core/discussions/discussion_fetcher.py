import structlog
from pydantic import BaseModel

from dagster_project.core.discussions.hn_client import HackerNewsClient
from dagster_project.core.discussions.hn_models import HNStoryFull
from dagster_project.core.discussions.lobsters_client import LobstersClient
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.shared_models import DiscussionLink

logger = structlog.get_logger()


class DiscussionFetchResult(BaseModel):
    hn_stories: list[tuple[int, HNStoryFull]]
    lobsters_stories: list[tuple[str, LobstersStoryFull]]
    discussion_links: list[DiscussionLink]


async def fetch_discussions_for_url(
    url: str,
    clients: list[HackerNewsClient | LobstersClient],
    pre_saved_links: list[DiscussionLink],
) -> DiscussionFetchResult:
    logger.info("discovering_discussions", url=url)

    hn_stories = []
    lobsters_stories = []
    all_discussion_links = []

    hn_story_ids_seen = set()
    lobsters_story_ids_seen = set()

    for client in clients:
        discussion_urls = await client.search_by_url(url)

        # Add pre-saved URLs that this client can handle
        for link in pre_saved_links:
            if client.can_handle(link.url):
                discussion_urls.append(link.url)

        # Fetch stories for this client
        if isinstance(client, HackerNewsClient):
            for disc_url in set(discussion_urls):
                story_id = client.extract_story_id(disc_url)
                if story_id in hn_story_ids_seen:
                    continue
                story_full = await client.fetch_story(disc_url, story_id)
                hn_stories.append((story_id, story_full))
                hn_story_ids_seen.add(story_id)
                all_discussion_links.append(client.build_discussion_link(story_id))

        elif isinstance(client, LobstersClient):
            for disc_url in set(discussion_urls):
                story_id = client.extract_story_id(disc_url)
                if story_id in lobsters_story_ids_seen:
                    continue
                story_full = await client.fetch_story(disc_url, story_id)
                lobsters_stories.append((story_id, story_full))
                lobsters_story_ids_seen.add(story_id)
                all_discussion_links.append(client.build_discussion_link(story_id))

    total_stories = len(hn_stories) + len(lobsters_stories)
    logger.info(
        "discussions_fetched",
        url=url,
        total_stories=total_stories,
        hn_stories=len(hn_stories),
        lobsters_stories=len(lobsters_stories),
    )

    return DiscussionFetchResult(
        hn_stories=hn_stories,
        lobsters_stories=lobsters_stories,
        discussion_links=all_discussion_links,
    )
