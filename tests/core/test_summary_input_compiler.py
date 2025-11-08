import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dagster_project.core.summary import compile_summary_input
from dagster_project.utils.url_utils import compute_url_hash


@pytest.fixture
def temp_bronze_dir(tmp_path):
    """Create a temporary bronze artifacts directory."""
    bronze_dir = tmp_path / "bronze"
    bronze_dir.mkdir()
    return bronze_dir


@pytest.fixture
def sample_html_url():
    """Sample HTML URL for testing."""
    return "https://example.com/article"


@pytest.fixture
def sample_youtube_url():
    """Sample YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def create_html_content(bronze_dir: Path, url: str, success: bool = True, content: str = "Test content"):
    """Helper to create HTML bronze content."""
    url_hash = compute_url_hash(url)
    raw_html_dir = bronze_dir / "raw_html"
    raw_html_dir.mkdir(exist_ok=True)

    data = {
        "url": url,
        "title": "Test Article",
        "content": content,
        "content_type": "html",
        "success": success,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if not success:
        data["error"] = "Extraction failed"

    file_path = raw_html_dir / f"{url_hash}.json"
    file_path.write_text(json.dumps(data))


def create_youtube_content(bronze_dir: Path, url: str, success: bool = True):
    """Helper to create YouTube bronze content."""
    url_hash = compute_url_hash(url)
    raw_youtube_dir = bronze_dir / "raw_youtube"
    raw_youtube_dir.mkdir(exist_ok=True)

    data = {
        "url": url,
        "title": "Test Video",
        "content": "Video description content",
        "content_type": "youtube",
        "success": success,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if not success:
        data["error"] = "Video extraction failed"

    file_path = raw_youtube_dir / f"{url_hash}.json"
    file_path.write_text(json.dumps(data))


def create_discussions(bronze_dir: Path, url: str):
    """Helper to create discussion bronze content."""
    url_hash = compute_url_hash(url)
    discussions_dir = bronze_dir / "discussions" / url_hash
    discussions_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "url": url,
        "total_stories": 2,
        "platforms": ["hackernews", "lobsters"],
        "hn_story_ids": [12345],
        "lobsters_story_ids": ["abc123"],
        "discussion_links": [
            {"type": "hackernews", "url": "https://news.ycombinator.com/item?id=12345"},
            {"type": "lobsters", "url": "https://lobste.rs/s/abc123"},
        ],
        "discovered_at": datetime.now(UTC).isoformat(),
        "cache_ttl_hours": 24,
    }

    metadata_path = discussions_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata))

    hn_story = {
        "id": 12345,
        "story_id": 12345,
        "title": "Test HN Story",
        "url": url,
        "author": "test_user",
        "points": 100,
        "created_at": datetime.now(UTC).isoformat(),
        "created_at_i": 1234567890,
        "children": [],
        "comment_count": 0,
    }
    hn_story_path = discussions_dir / "12345.json"
    hn_story_path.write_text(json.dumps(hn_story))

    lobsters_story = {
        "short_id": "abc123",
        "title": "Test Lobsters Story",
        "url": url,
        "score": 50,
        "created_at": datetime.now(UTC).isoformat(),
        "submitter_user": "test_user",
        "user_is_author": False,
        "tags": ["programming"],
        "description": "Test description",
        "description_plain": "Test description",
        "short_id_url": "https://lobste.rs/s/abc123",
        "comments_url": "https://lobste.rs/s/abc123/comments",
        "comments": [],
        "comment_count": 0,
    }
    lobsters_story_path = discussions_dir / "abc123.json"
    lobsters_story_path.write_text(json.dumps(lobsters_story))


def test_compile_summary_input_html_success(temp_bronze_dir, sample_html_url):
    """Test successful compilation with HTML content."""
    create_html_content(temp_bronze_dir, sample_html_url)

    result = compile_summary_input(sample_html_url, str(temp_bronze_dir))

    assert result.url == sample_html_url
    assert result.title == "Test Article"
    assert result.content == "Test content"
    assert result.content_type == "html"
    assert result.discussions is None


def test_compile_summary_input_youtube_success(temp_bronze_dir, sample_youtube_url):
    """Test successful compilation with YouTube content."""
    create_youtube_content(temp_bronze_dir, sample_youtube_url)

    result = compile_summary_input(sample_youtube_url, str(temp_bronze_dir))

    assert result.url == sample_youtube_url
    assert result.title == "Test Video"
    assert result.content == "Video description content"
    assert result.content_type == "youtube"
    assert result.discussions is None


def test_compile_summary_input_with_discussions(temp_bronze_dir, sample_html_url):
    """Test compilation with discussions present."""
    create_html_content(temp_bronze_dir, sample_html_url)
    create_discussions(temp_bronze_dir, sample_html_url)

    result = compile_summary_input(sample_html_url, str(temp_bronze_dir))

    assert result.discussions is not None
    assert len(result.discussions) == 2
    assert result.discussions[0]["story_id"] == 12345
    assert result.discussions[1]["short_id"] == "abc123"


def test_compile_summary_input_missing_bronze_content(temp_bronze_dir, sample_html_url):
    """Test exception when bronze content doesn't exist."""
    with pytest.raises(ValueError, match="No bronze content found"):
        compile_summary_input(sample_html_url, str(temp_bronze_dir))


def test_compile_summary_input_failed_extraction(temp_bronze_dir, sample_html_url):
    """Test exception when extraction failed."""
    create_html_content(temp_bronze_dir, sample_html_url, success=False)

    with pytest.raises(ValueError, match="Extraction failed"):
        compile_summary_input(sample_html_url, str(temp_bronze_dir))


def test_compile_summary_input_without_discussions(temp_bronze_dir, sample_html_url):
    """Test compilation without discussions (discussions=None)."""
    create_html_content(temp_bronze_dir, sample_html_url)

    result = compile_summary_input(sample_html_url, str(temp_bronze_dir))

    assert result.discussions is None


def test_compile_summary_input_discussion_loading_error(temp_bronze_dir, sample_html_url):
    """Test exception when discussion loading fails (corrupted data)."""
    create_html_content(temp_bronze_dir, sample_html_url)

    url_hash = compute_url_hash(sample_html_url)
    discussions_dir = temp_bronze_dir / "discussions" / url_hash
    discussions_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = discussions_dir / "metadata.json"
    metadata_path.write_text("invalid json {")

    with pytest.raises(ValueError, match="Failed to load discussions"):
        compile_summary_input(sample_html_url, str(temp_bronze_dir))
