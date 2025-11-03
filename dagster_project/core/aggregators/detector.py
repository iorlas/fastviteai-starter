from urllib.parse import urlparse

from pydantic import BaseModel


class AggregatorPattern(BaseModel):
    domain: str
    name: str
    url_pattern: str | None = None


AGGREGATORS = [
    AggregatorPattern(domain="news.ycombinator.com", name="hackernews", url_pattern="/item"),
]


def is_aggregator_url(url: str) -> tuple[bool, str | None]:
    parsed = urlparse(url)

    for pattern in AGGREGATORS:
        if pattern.domain in parsed.netloc:
            if pattern.url_pattern:
                if pattern.url_pattern in parsed.path:
                    return True, pattern.name
            else:
                return True, pattern.name

    return False, None
