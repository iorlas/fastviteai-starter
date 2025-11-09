import html
import json
import re
from pathlib import Path

from dagster_project.core.discussions.hn_models import HNStoryFull
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.shared_models import DiscussionMetadata
from dagster_project.core.summary.summarizer import SummaryInput
from dagster_project.utils.tables import BronzeTable
from dagster_project.utils.url_utils import compute_url_hash


def _clean_html(text: str) -> str:
    """Remove HTML tags and decode entities from text."""
    # Decode HTML entities (&#x27; -> ', &quot; -> ", etc.)
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
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

    return SummaryInput(
        content=content,
        title=title,
        content_type=content_type,
        url=url,
        discussions=discussions_data,
    )


def _load_bronze_content(base_path: Path, url_hash: str, url: str) -> dict:
    for partition in [BronzeTable.HTML, BronzeTable.YOUTUBE]:
        file_path = base_path / partition / f"{url_hash}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())

    raise ValueError(f"No bronze content found for {url} (hash: {url_hash})")


def _slim_comment(comment_data: dict, text_field: str = "text", author_field: str = "author", id_field: str = "id", points_field: str = "points") -> list | None:
    """Convert comment to minimal array: [author, text, ?children].

    Strips HTML and removes ID/points for compactness while keeping author context.
    """
    text = comment_data.get(text_field)
    author = comment_data.get(author_field)

    if not text or not author:
        return None

    # Clean HTML entities and tags from text
    clean_text = _clean_html(text)

    # Base array: author and text
    result = [author, clean_text]

    # Process children recursively
    if children := comment_data.get("children"):
        slim_children = [_slim_comment(child, text_field, author_field, id_field, points_field) for child in children]
        slim_children = [c for c in slim_children if c is not None]
        if slim_children:
            result.append(slim_children)

    return result


def _load_discussions(base_path: Path, url_hash: str) -> list[dict] | None:
    metadata_path = base_path / BronzeTable.DISCUSSIONS / url_hash / "metadata.json"

    if not metadata_path.exists():
        return None

    try:
        metadata_dict = json.loads(metadata_path.read_text())
        metadata = DiscussionMetadata(**metadata_dict)

        slim_discussions = []

        for link in metadata.discussion_links:
            if link.type == "hackernews":
                story_id = int(link.url.split("id=")[1].split("&")[0])
                story_path = base_path / BronzeTable.DISCUSSIONS / url_hash / f"{story_id}.json"
                story_data = json.loads(story_path.read_text())
                story = HNStoryFull(**story_data)

                # Discussion object with labeled fields, children as arrays
                discussion = {
                    "id": story.id,
                    "author": story.author,
                    "points": story.points,
                }

                if story.children:
                    slim_children = [_slim_comment(c.model_dump()) for c in story.children]
                    slim_children = [c for c in slim_children if c is not None]
                    if slim_children:
                        discussion["children"] = slim_children

                slim_discussions.append(discussion)

            elif link.type == "lobsters":
                story_id = link.url.split("/s/")[1].split("/")[0]
                story_path = base_path / BronzeTable.DISCUSSIONS / url_hash / f"{story_id}.json"
                story_data = json.loads(story_path.read_text())
                story = LobstersStoryFull(**story_data)

                # Discussion object with labeled fields, children as arrays
                discussion = {
                    "id": story.short_id,
                    "author": story.submitter_user,
                    "points": story.score,
                }

                if story.comments:
                    slim_children = [_slim_comment(c.model_dump(), text_field="comment_plain", author_field="commenting_user", id_field="short_id", points_field="score") for c in story.comments]
                    slim_children = [c for c in slim_children if c is not None]
                    if slim_children:
                        discussion["children"] = slim_children

                slim_discussions.append(discussion)

        return slim_discussions

    except Exception as e:
        raise ValueError(f"Failed to load discussions for hash {url_hash}: {e}") from e
