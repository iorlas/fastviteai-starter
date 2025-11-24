import structlog

from ailabbrains.core.discussions.hn_client import HackerNewsClient
from ailabbrains.core.discussions.lobsters_client import LobstersClient
from ailabbrains.core.discussions.shared_models import DiscussionLink

logger = structlog.get_logger()

HANDLERS = [HackerNewsClient, LobstersClient]


async def resolve_url(url: str) -> tuple[str, DiscussionLink | None]:
    for client_class in HANDLERS:
        if client_class.can_handle(url):
            client = client_class()
            result = await client.extract_article_url(url)

            logger.info(
                "aggregator.resolved",
                original_url=url,
                resolved_url=result.article_url,
                aggregator_type=client_class.platform_name(),
                title=result.title,
            )

            discussion_link = DiscussionLink(
                type=client_class.platform_name(),
                url=url,
            )

            return (result.article_url, discussion_link)

    return (url, None)
