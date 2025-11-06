from enum import Enum
from urllib.parse import urlparse


class ContentType(str, Enum):
    YOUTUBE = "youtube"
    HTML = "html"


def detect_content_type(url: str) -> ContentType:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    youtube_domains = {
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com",
    }

    if netloc in youtube_domains:
        return ContentType.YOUTUBE

    return ContentType.HTML
