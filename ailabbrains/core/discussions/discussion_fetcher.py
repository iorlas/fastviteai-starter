from typing import Literal, cast

import structlog
from pydantic import BaseModel

from ailabbrains.core.discussions.hn_client import HackerNewsClient
from ailabbrains.core.discussions.lobsters_client import LobstersClient
from ailabbrains.core.discussions.shared_models import DiscussionLink
from ailabbrains.core.discussions.unified_models import UnifiedDiscussion

logger = structlog.get_logger()


class DiscussionFetchResult(BaseModel):
    discussions: list[UnifiedDiscussion]
    discussion_links: list[DiscussionLink]


async def fetch_discussions_for_url(
    url: str,
    clients: list[HackerNewsClient | LobstersClient],
    pre_saved_links: list[DiscussionLink],
) -> DiscussionFetchResult:
    logger.info("discovering_discussions", url=url)

    discussions = []
    all_discussion_links = []
    story_ids_seen = set()

    for client in clients:
        discussion_urls = await client.search_by_url(url)

        # Add pre-saved URLs that this client can handle
        for link in pre_saved_links:
            if client.can_handle(link.url):
                discussion_urls.append(link.url)

        # Fetch unified discussions from any client
        for disc_url in set(discussion_urls):
            # Use platform + URL as dedup key
            dedup_key = f"{client.platform_name()}:{disc_url}"
            if dedup_key in story_ids_seen:
                continue

            discussion = await client.fetch_story(disc_url)
            discussions.append(discussion)
            story_ids_seen.add(dedup_key)

            # Build link from discussion data
            platform = cast(Literal["hackernews", "lobsters"], discussion.platform)
            link = DiscussionLink(type=platform, url=discussion.discussion_url)
            all_discussion_links.append(link)

    logger.info(
        "discussions_fetched",
        url=url,
        total_discussions=len(discussions),
    )

    return DiscussionFetchResult(
        discussions=discussions,
        discussion_links=all_discussion_links,
    )
