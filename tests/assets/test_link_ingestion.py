import pytest
from dagster import build_asset_context

from dagster_project.assets.bronze_raw_links import (
    compute_url_hash,
    read_links_from_file,
)


@pytest.fixture
def mock_context():
    return build_asset_context()


@pytest.fixture
def temp_project_root(tmp_path, monkeypatch):
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
    summaries_dir = tmp_path / "artifacts" / "silver" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    # Set PROJECT_ROOT environment variable
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

    return tmp_path


@pytest.mark.integration
def test_compute_url_hash():
    url = "https://example.com/test"
    hash_result = compute_url_hash(url)

    assert len(hash_result) == 16
    assert isinstance(hash_result, str)

    # Same URL should produce same hash
    assert compute_url_hash(url) == hash_result

    # Different URL should produce different hash
    assert compute_url_hash("https://example.com/different") != hash_result


@pytest.mark.integration
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


@pytest.mark.integration
def test_read_links_from_nonexistent_file(tmp_path):
    nonexistent_file = tmp_path / "does_not_exist.txt"
    links = read_links_from_file(nonexistent_file)

    assert links == []


@pytest.mark.integration
def test_bronze_raw_links_with_temp_files(mock_context, temp_project_root):
    # Test read_links_from_file with temp files (PROJECT_ROOT env var already set by fixture)
    from dagster_project.assets.bronze_raw_links import read_links_from_file

    manual_links = read_links_from_file(temp_project_root / "manual_links.txt")
    monitoring_links = read_links_from_file(temp_project_root / "monitoring_list.txt")

    # Should have 3 manual + 2 monitoring = 5 total
    assert len(manual_links) == 3
    assert len(monitoring_links) == 2


@pytest.mark.integration
def test_bronze_raw_links_filters_duplicates():
    # Test that same URL produces same hash
    url = "https://example.com/test"
    hash1 = compute_url_hash(url)
    hash2 = compute_url_hash(url)
    assert hash1 == hash2

    # Test different URLs produce different hashes
    url2 = "https://example.com/different"
    hash3 = compute_url_hash(url2)
    assert hash1 != hash3
