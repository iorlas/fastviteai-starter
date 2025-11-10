import html
import json
import re
from pathlib import Path

from dagster_project.core.summary.summarizer import DiscussionMetadata, SummaryInput
from dagster_project.utils.tables import BronzeTable
from dagster_project.utils.url_utils import compute_url_hash


def _clean_html(text: str) -> str:
    # Decode HTML entities (&#x27; -> ', &quot; -> ", etc.)
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def compile_summary_input(url: str, artifacts_base_path: str) -> SummaryInput:
    url_hash = compute_url_hash(url)
    base_path = Path(artifacts_base_path)

    extracted_content = _load_bronze_content(base_path, url_hash, url)

    if not extracted_content.get("success"):
        error_msg = extracted_content.get("error", "Content extraction failed")
        raise ValueError(f"Extraction failed for {url}: {error_msg}")

    title = extracted_content.get("title", url)
    content = extracted_content.get("content", "")
    content_type = extracted_content.get("content_type", "unknown")

    discussions_data = _load_discussions(base_path, url_hash)
    discussions_text = _format_discussion_as_text(discussions_data) if discussions_data else None
    discussions_count = len(discussions_data) if discussions_data else None
    discussions_metadata = _extract_discussions_metadata(discussions_data) if discussions_data else None

    return SummaryInput(
        content=content,
        title=title,
        content_type=content_type,
        url=url,
        discussions=discussions_text,
        discussions_count=discussions_count,
        discussions_metadata=discussions_metadata,
    )


def _load_bronze_content(base_path: Path, url_hash: str, url: str) -> dict:
    for partition in [BronzeTable.HTML, BronzeTable.YOUTUBE]:
        file_path = base_path / partition / f"{url_hash}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())

    raise ValueError(f"No bronze content found for {url} (hash: {url_hash})")


def _slim_comment(comment_data: dict) -> list | None:
    # Try multiple field name variants for backwards compatibility
    text = comment_data.get("text") or comment_data.get("comment_plain")
    author = comment_data.get("author") or comment_data.get("commenting_user")

    if not text or not author:
        return None

    # Clean HTML entities and tags from text
    clean_text = _clean_html(text)

    # Base array: author and text
    result = [author, clean_text]

    # Process children recursively
    if children := comment_data.get("children"):
        slim_children = [_slim_comment(child) for child in children]
        slim_children = [c for c in slim_children if c is not None]
        if slim_children:
            result.append(slim_children)

    return result


def _format_comment_thread(comments: list, indent_level: int = 0) -> str:
    lines = []
    tabs = "\t" * indent_level

    for comment in comments:
        if not comment or len(comment) < 2:
            continue

        author, text = comment[0], comment[1]
        lines.append(f"{tabs}{author}: {text}")

        # Recursively format children if present
        if len(comment) > 2 and comment[2]:
            children_text = _format_comment_thread(comment[2], indent_level + 1)
            if children_text:
                lines.append(children_text)

    return "\n".join(lines)


def _format_discussion_as_text(discussions: list[dict]) -> str:
    if not discussions:
        return ""

    formatted_discussions = []

    for idx, discussion in enumerate(discussions, 1):
        lines = []

        # Header with story metadata
        author = discussion.get("author", "unknown")
        points = discussion.get("points", 0)
        lines.append(f"Discussion {idx}:")
        lines.append(f"Story by {author} ({points} points)")
        lines.append("")

        # Format comment threads
        if children := discussion.get("children"):
            comment_text = _format_comment_thread(children)
            if comment_text:
                lines.append(comment_text)

        formatted_discussions.append("\n".join(lines))

    return "\n\n".join(formatted_discussions)


def _extract_discussions_metadata(discussions: list[dict]) -> list[DiscussionMetadata]:
    return [
        DiscussionMetadata(
            platform=d["platform"],
            url=d["discussion_url"],  # Use unified field name
            title=d["title"],
            points=d["points"],
            comment_count=d["comment_count"],
        )
        for d in discussions
    ]


def _load_discussions(base_path: Path, url_hash: str) -> list[dict] | None:
    discussions_dir = base_path / BronzeTable.DISCUSSIONS / url_hash

    if not discussions_dir.exists():
        return None

    try:
        # Load all discussion JSON files (skip metadata.json)
        discussions = []

        for file_path in discussions_dir.glob("*.json"):
            if file_path.name == "metadata.json":
                continue

            # Load unified discussion directly (no parsing/conversion needed)
            discussion = json.loads(file_path.read_text())

            # Process comments into slim format for LLM consumption
            if comments := discussion.get("comments"):
                slim_children = [_slim_comment(c) for c in comments]
                slim_children = [c for c in slim_children if c is not None]
                # Replace full comment objects with slim arrays
                discussion["children"] = slim_children if slim_children else []

            discussions.append(discussion)

        return discussions if discussions else None

    except Exception as e:
        raise ValueError(f"Failed to load discussions for hash {url_hash}: {e}") from e
