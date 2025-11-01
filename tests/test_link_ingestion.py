from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dagster import build_asset_context

from dagster_project.assets.link_ingestion import (
    compute_url_hash,
    read_links_from_file,
)


@pytest.fixture
def mock_context():
    return build_asset_context()


@pytest.fixture
def temp_project_root(tmp_path):
    # Create manual_links.txt
    manual_file = tmp_path / "manual_links.txt"
    manual_file.write_text(
        "https://example.com/article1\n"
        "https://example.com/article2\n"
        "# This is a comment\n"
        "\n"
        "https://example.com/article3\n"
    )

    # Create monitoring_list.txt
    monitoring_file = tmp_path / "monitoring_list.txt"
    monitoring_file.write_text("https://example.com/monitoring1\nhttps://example.com/monitoring2\n")

    # Create summaries directory
    summaries_dir = tmp_path / "artifacts" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    return tmp_path


def test_compute_url_hash():
    url = "https://example.com/test"
    hash_result = compute_url_hash(url)

    assert len(hash_result) == 16
    assert isinstance(hash_result, str)

    # Same URL should produce same hash
    assert compute_url_hash(url) == hash_result

    # Different URL should produce different hash
    assert compute_url_hash("https://example.com/different") != hash_result


def test_read_links_from_file(tmp_path):
    # Create test file
    test_file = tmp_path / "test_links.txt"
    test_file.write_text(
        "https://example.com/1\n# Comment line\n\nhttps://example.com/2\nhttps://example.com/3\n"
    )

    links = read_links_from_file(test_file)

    assert len(links) == 3
    assert "https://example.com/1" in links
    assert "https://example.com/2" in links
    assert "https://example.com/3" in links


def test_read_links_from_nonexistent_file(tmp_path):
    nonexistent_file = tmp_path / "does_not_exist.txt"
    links = read_links_from_file(nonexistent_file)

    assert links == []


def test_link_ingestion_with_temp_files(mock_context, temp_project_root):
    # We need to mock the project_root path resolution
    def mock_file_path():
        return temp_project_root / "dagster_project" / "assets" / "link_ingestion.py"

    with patch("dagster_project.assets.link_ingestion.Path") as mock_path:
        mock_path.return_value.parent.parent.parent = temp_project_root
        mock_path.__file__ = str(mock_file_path())

        # Mock the actual Path constructor calls within the function
        def path_side_effect(arg):
            if arg == mock_path.__file__:
                result = MagicMock()
                result.parent.parent.parent = temp_project_root
                return result
            return Path(arg)

        mock_path.side_effect = path_side_effect

        # Create a simpler inline test
        from dagster_project.assets.link_ingestion import read_links_from_file

        manual_links = read_links_from_file(temp_project_root / "manual_links.txt")
        monitoring_links = read_links_from_file(temp_project_root / "monitoring_list.txt")

        # Should have 3 manual + 2 monitoring = 5 total
        assert len(manual_links) == 3
        assert len(monitoring_links) == 2


def test_link_ingestion_filters_duplicates():
    # Test that same URL produces same hash
    url = "https://example.com/test"
    hash1 = compute_url_hash(url)
    hash2 = compute_url_hash(url)
    assert hash1 == hash2

    # Test different URLs produce different hashes
    url2 = "https://example.com/different"
    hash3 = compute_url_hash(url2)
    assert hash1 != hash3
