"""Content extraction asset for routing URLs to appropriate extractors."""

import json
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

from dagster import AssetExecutionContext, Field, asset

from dagster_project.assets.link_ingestion import LinkRecord
from dagster_project.ops.html_extractor import (
    HTMLExtractionError,
    extract_html_content,
)
from dagster_project.ops.youtube_extractor import (
    YouTubeExtractionError,
    extract_youtube_content,
)


class ExtractedContent(NamedTuple):
    """Content extracted from a URL.

    Attributes:
        url: Original URL
        url_hash: SHA256 hash of the URL
        content_type: Type of content (html or youtube)
        title: Content title
        text: Main text content (article or transcript)
        metadata: Additional metadata
        extraction_success: Whether extraction succeeded
        error_message: Error message if extraction failed
    """

    url: str
    url_hash: str
    content_type: str
    title: str
    text: str
    metadata: dict
    extraction_success: bool
    error_message: str | None


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube video.

    Args:
        url: The URL to check

    Returns:
        True if URL is a YouTube video
    """
    parsed = urlparse(url)
    return parsed.netloc in ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"]


def save_extracted_content(
    content: ExtractedContent,
    output_dir: Path,
) -> None:
    """Save extracted content to JSON file.

    Args:
        content: Extracted content object
        output_dir: Directory to save to (html/ or videos/)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{content.url_hash}.json"

    data = {
        "url": content.url,
        "url_hash": content.url_hash,
        "content_type": content.content_type,
        "title": content.title,
        "text": content.text,
        "metadata": content.metadata,
        "extraction_success": content.extraction_success,
        "error_message": content.error_message,
    }

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


@asset(
    name="content_extraction",
    deps=["link_ingestion"],
    config_schema={
        "project_root": Field(str, is_required=False),
    },
)
def content_extraction_asset(
    context: AssetExecutionContext,
    link_ingestion: list[LinkRecord],
) -> list[ExtractedContent]:
    """Extract content from URLs using appropriate extractors.

    Routes URLs to HTML or YouTube extractors based on URL pattern.
    Saves extracted content to artifacts/html/ or artifacts/videos/.

    Config:
        project_root: Path to project root directory (default: auto-detected from __file__)

    Args:
        context: Dagster execution context
        link_ingestion: List of links from link_ingestion asset

    Returns:
        List of ExtractedContent objects
    """
    # Get project root from config or auto-detect
    project_root_str = context.op_config.get("project_root")
    if project_root_str:
        project_root = Path(project_root_str)
    else:
        project_root = Path(__file__).parent.parent.parent
    html_dir = project_root / "artifacts" / "html"
    videos_dir = project_root / "artifacts" / "videos"

    extracted_contents = []

    for link_record in link_ingestion:
        url = link_record.url
        url_hash = link_record.url_hash

        context.log.info(f"Extracting content from: {url}")

        try:
            if is_youtube_url(url):
                # Extract YouTube content
                yt_content = extract_youtube_content(url)

                extracted = ExtractedContent(
                    url=url,
                    url_hash=url_hash,
                    content_type="youtube",
                    title=yt_content.title,
                    text=yt_content.transcript,
                    metadata={
                        "channel": yt_content.channel,
                        "duration": yt_content.duration,
                        "description": yt_content.description,
                        **yt_content.metadata,
                    },
                    extraction_success=True,
                    error_message=None,
                )

                # Save to videos directory
                save_extracted_content(extracted, videos_dir)

            else:
                # Extract HTML content
                html_content = extract_html_content(url)

                extracted = ExtractedContent(
                    url=url,
                    url_hash=url_hash,
                    content_type="html",
                    title=html_content.title,
                    text=html_content.content,
                    metadata={
                        "author": html_content.author,
                        "publish_date": html_content.publish_date,
                        **html_content.metadata,
                    },
                    extraction_success=True,
                    error_message=None,
                )

                # Save to html directory
                save_extracted_content(extracted, html_dir)

            extracted_contents.append(extracted)
            context.log.info(f"Successfully extracted: {extracted.title}")

        except (HTMLExtractionError, YouTubeExtractionError) as e:
            # Create error record
            extracted = ExtractedContent(
                url=url,
                url_hash=url_hash,
                content_type="youtube" if is_youtube_url(url) else "html",
                title="Extraction Failed",
                text="",
                metadata={},
                extraction_success=False,
                error_message=str(e),
            )

            # Save error record
            output_dir = videos_dir if is_youtube_url(url) else html_dir
            save_extracted_content(extracted, output_dir)

            extracted_contents.append(extracted)
            context.log.warning(f"Extraction failed for {url}: {e}")

    # Log metadata
    successful = sum(1 for c in extracted_contents if c.extraction_success)
    failed = len(extracted_contents) - successful

    context.add_output_metadata(
        {
            "total_extracted": len(extracted_contents),
            "successful": successful,
            "failed": failed,
            "html_count": sum(1 for c in extracted_contents if c.content_type == "html"),
            "youtube_count": sum(1 for c in extracted_contents if c.content_type == "youtube"),
        }
    )

    return extracted_contents
