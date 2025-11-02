from pathlib import Path

import pytest


@pytest.mark.integration
def test_bronze_layer_structure():
    """Verify bronze layer directory structure exists."""
    bronze_dir = Path("artifacts/bronze")
    assert bronze_dir.exists(), "Bronze layer directory should exist"
    assert bronze_dir.is_dir(), "Bronze layer should be a directory"

    raw_links_dir = bronze_dir / "raw_links"
    assert raw_links_dir.exists(), "Bronze raw_links subdirectory should exist"
    assert raw_links_dir.is_dir(), "raw_links should be a directory"

    raw_html_dir = bronze_dir / "raw_html"
    assert raw_html_dir.exists(), "Bronze raw_html subdirectory should exist"
    assert raw_html_dir.is_dir(), "raw_html should be a directory"


@pytest.mark.integration
def test_silver_layer_structure():
    """Verify silver layer directory structure exists."""
    silver_dir = Path("artifacts/silver")
    assert silver_dir.exists(), "Silver layer directory should exist"
    assert silver_dir.is_dir(), "Silver layer should be a directory"

    extracted_content_dir = silver_dir / "extracted_content"
    assert extracted_content_dir.exists(), "Silver extracted_content subdirectory should exist"
    assert extracted_content_dir.is_dir(), "extracted_content should be a directory"

    summaries_dir = silver_dir / "summaries"
    assert summaries_dir.exists(), "Silver summaries subdirectory should exist"
    assert summaries_dir.is_dir(), "summaries should be a directory"


@pytest.mark.integration
def test_directory_permissions():
    """Verify created directories have correct read/write permissions."""
    bronze_dir = Path("artifacts/bronze")
    silver_dir = Path("artifacts/silver")

    assert bronze_dir.stat().st_mode & 0o700 != 0, "Bronze directory should be readable/writable"
    assert silver_dir.stat().st_mode & 0o700 != 0, "Silver directory should be readable/writable"

    for subdir in ["raw_links", "raw_html"]:
        subdir_path = bronze_dir / subdir
        assert subdir_path.stat().st_mode & 0o700 != 0, (
            f"Bronze {subdir} should be readable/writable"
        )

    for subdir in ["extracted_content", "summaries"]:
        subdir_path = silver_dir / subdir
        assert subdir_path.stat().st_mode & 0o700 != 0, (
            f"Silver {subdir} should be readable/writable"
        )


@pytest.mark.integration
def test_directory_structure_isolation():
    """Verify new medallion directories don't interfere with existing legacy structure."""
    artifacts_dir = Path("artifacts")
    assert artifacts_dir.exists(), "Root artifacts directory should exist"

    legacy_dirs = ["html", "videos", "summaries"]
    for legacy_dir in legacy_dirs:
        legacy_path = artifacts_dir / legacy_dir
        assert legacy_path.exists(), f"Legacy {legacy_dir} directory should still exist"
        assert legacy_path.is_dir(), f"Legacy {legacy_dir} should be a directory"

    bronze_dir = artifacts_dir / "bronze"
    silver_dir = artifacts_dir / "silver"
    assert bronze_dir.exists(), "Bronze directory should coexist with legacy structure"
    assert silver_dir.exists(), "Silver directory should coexist with legacy structure"
