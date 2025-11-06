from datetime import UTC, datetime
from typing import NamedTuple

import httpx
import trafilatura


class HTMLContent(NamedTuple):
    url: str
    title: str
    content: str
    author: str | None
    publish_date: str | None
    metadata: dict


class HTMLExtractionError(Exception):
    pass


def extract_html_from_cached(html_content: str, url: str) -> HTMLContent:
    try:
        metadata_obj = trafilatura.extract_metadata(html_content)
        content = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        title = (metadata_obj.title if metadata_obj else None) or "Untitled"
        author = metadata_obj.author if metadata_obj else None
        publish_date = metadata_obj.date if metadata_obj else None

        extracted_at = datetime.now(UTC).isoformat()
        metadata = {
            "content_length": len(content or ""),
            "extracted_at": extracted_at,
        }

        return HTMLContent(
            url=url,
            title=title,
            content=content or "",
            author=author,
            publish_date=publish_date,
            metadata=metadata,
        )

    except Exception as e:
        raise HTMLExtractionError(f"Error extracting content from {url}: {e}") from e


def extract_html_content(url: str, timeout: int = 30, html_content: str | None = None) -> HTMLContent:
    if html_content:
        return extract_html_from_cached(html_content, url)

    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()

        metadata_obj = trafilatura.extract_metadata(response.text)
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        title = (metadata_obj.title if metadata_obj else None) or "Untitled"
        author = metadata_obj.author if metadata_obj else None
        publish_date = metadata_obj.date if metadata_obj else None

        extracted_at = datetime.now(UTC).isoformat()
        metadata = {
            "content_length": len(content or ""),
            "extracted_at": extracted_at,
            "final_url": str(response.url),
        }

        return HTMLContent(
            url=url,
            title=title,
            content=content or "",
            author=author,
            publish_date=publish_date,
            metadata=metadata,
        )

    except httpx.HTTPError as e:
        raise HTMLExtractionError(f"HTTP error fetching {url}: {e}") from e
    except Exception as e:
        raise HTMLExtractionError(f"Error extracting content from {url}: {e}") from e
