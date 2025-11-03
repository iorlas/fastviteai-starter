import structlog
from bs4 import BeautifulSoup

from dagster_project.core.aggregators.base import AggregatorExtractor, ExtractionResult
from dagster_project.core.cache.http_cache import HTTPCache

logger = structlog.get_logger()


class HackerNewsExtractor(AggregatorExtractor):
    def __init__(self, http_cache: HTTPCache | None = None):
        self.http_cache = http_cache or HTTPCache()

    def extract_article_url(self, hn_url: str) -> ExtractionResult:
        logger.info("hn_extraction_start", url=hn_url)

        try:
            html_content = self.http_cache.fetch(hn_url, ttl_seconds=None)

            soup = BeautifulSoup(html_content, "html.parser")

            titleline = soup.find("span", class_="titleline")
            if not titleline:
                raise ValueError("Could not find titleline element in HN page")

            link = titleline.find("a")
            if not link or not link.get("href"):
                raise ValueError("Could not find article link in titleline")

            article_url = link["href"]
            title = link.get_text(strip=True)

            if article_url.startswith("item?"):
                logger.info("hn_self_post_detected", hn_url=hn_url, title=title, type="self_post")
                return ExtractionResult(article_url=hn_url, title=title)

            logger.info(
                "hn_extraction_success",
                hn_url=hn_url,
                article_url=article_url,
                title=title,
            )

            return ExtractionResult(article_url=article_url, title=title)

        except Exception as e:
            logger.error("hn_extraction_failed", url=hn_url, error=str(e))
            raise
