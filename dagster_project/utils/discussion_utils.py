import json
from pathlib import Path


def count_comments_recursive(comments: list) -> int:
    """Recursively count all comments in tree structure."""
    count = len(comments)
    for comment in comments:
        if hasattr(comment, "children") and comment.children:
            count += count_comments_recursive(comment.children)
    return count


def load_stories_from_dir[T, IDType: (str, int)](
    url_dir: Path,
    story_ids: list[IDType],
    story_class: type[T],
    platform_name: str,
    log_callback=None,
) -> list[T]:
    """Load story files from directory, parse into story objects.

    Args:
        url_dir: Directory containing story JSON files
        story_ids: List of story IDs to load
        story_class: Pydantic model class to parse stories into
        platform_name: Platform name for logging (e.g., "hackernews", "lobsters")
        log_callback: Optional callback for logging (receives message string)

    Returns:
        List of parsed story objects
    """
    stories = []
    for story_id in story_ids:
        story_file = url_dir / f"{story_id}.json"

        if not story_file.exists():
            if log_callback:
                log_callback(f"Story file missing: {story_id} ({platform_name})")
            continue

        with story_file.open() as f:
            story_dict = json.load(f)

        story = story_class(**story_dict)
        stories.append(story)

        if log_callback:
            log_callback(f"Story loaded: {story_id} ({platform_name})")

    return stories
