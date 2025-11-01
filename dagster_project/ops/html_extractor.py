from datetime import UTC, datetime
from typing import NamedTuple

import httpx
from bs4 import BeautifulSoup


class HTMLContent(NamedTuple):
    url: str
    title: str
    content: str
    author: str | None
    publish_date: str | None
    metadata: dict


class HTMLExtractionError(Exception):
    pass


def extract_html_content(url: str, timeout: int = 30) -> HTMLContent:
    try:
        # Fetch HTML content
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "iframe", "nav", "footer", "aside"]):
            element.decompose()

        # Remove common ad/tracking elements
        for class_name in ["advertisement", "ad-container", "social-share", "comments"]:
            for element in soup.find_all(class_=lambda x: x and class_name in x.lower()):
                element.decompose()

        # Extract title
        title = _extract_title(soup)

        # Extract main content
        content = _extract_content(soup)

        # Extract metadata
        author = _extract_author(soup)
        publish_date = _extract_publish_date(soup)

        # Build metadata dict
        extracted_at = datetime.now(UTC).isoformat()
        metadata = {
            "content_length": len(content),
            "extracted_at": extracted_at,
            "final_url": str(response.url),
        }

        return HTMLContent(
            url=url,
            title=title,
            content=content,
            author=author,
            publish_date=publish_date,
            metadata=metadata,
        )

    except httpx.HTTPError as e:
        raise HTMLExtractionError(f"HTTP error fetching {url}: {e}") from e
    except Exception as e:
        raise HTMLExtractionError(f"Error extracting content from {url}: {e}") from e


def _extract_title(soup: BeautifulSoup) -> str:
    # Try common title selectors in order
    selectors = [
        ("h1", {"class_": lambda x: x and "title" in x.lower()}),
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
        ("title", {}),
        ("h1", {}),
    ]

    for tag, attrs in selectors:
        if tag == "meta":
            element = soup.find(tag, attrs=attrs)
            if element and element.get("content"):
                return element["content"].strip()
        else:
            element = soup.find(tag, attrs=attrs) if attrs else soup.find(tag)
            if element and element.get_text():
                return element.get_text().strip()

    return "Untitled"


def _extract_content(soup: BeautifulSoup) -> str:
    # Try common content containers in order
    selectors = [
        ("article", {}),
        ("div", {"class_": lambda x: x and "content" in x.lower()}),
        ("div", {"class_": lambda x: x and "article" in x.lower()}),
        ("main", {}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs=attrs) if attrs else soup.find(tag)
        if element:
            # Extract text and clean whitespace
            text = element.get_text(separator="\n", strip=True)
            # Remove excessive newlines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n\n".join(lines)

    # Fallback: get all paragraphs
    paragraphs = soup.find_all("p")
    if paragraphs:
        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if text:
            return text

    # Last resort: body text
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n\n".join(lines)

    return ""


def _extract_author(soup: BeautifulSoup) -> str | None:
    selectors = [
        ("meta", {"name": "author"}),
        ("meta", {"property": "article:author"}),
        ("a", {"rel": "author"}),
        ("span", {"class_": lambda x: x and "author" in x.lower()}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs=attrs)
        if element:
            if tag == "meta" and element.get("content"):
                return element["content"].strip()
            elif text := element.get_text():
                return text.strip()

    return None


def _extract_publish_date(soup: BeautifulSoup) -> str | None:
    selectors = [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "publish_date"}),
        ("meta", {"name": "date"}),
        ("time", {"datetime": True}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs=attrs)
        if element:
            if tag == "meta" and element.get("content"):
                return element["content"].strip()
            elif tag == "time" and element.get("datetime"):
                return element["datetime"].strip()

    return None
