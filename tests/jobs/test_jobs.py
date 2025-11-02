from unittest.mock import PropertyMock

import pytest
from dagster import build_asset_context

from dagster_project.assets.bronze_raw_links import bronze_raw_links


@pytest.fixture
def temp_env_with_files(tmp_path):
    # Create input files with different links
    manual_file = tmp_path / "manual_links.txt"
    manual_file.write_text(
        "# Manual links\n"
        "https://example.com/manual-article-1\n"
        "https://example.com/manual-article-2\n"
    )

    monitoring_file = tmp_path / "monitoring_list.txt"
    monitoring_file.write_text(
        "# Monitoring links\n"
        "https://example.com/monitoring-article-1\n"
        "https://www.youtube.com/watch?v=monitoring-video-1\n"
    )

    # Create artifact directories
    (tmp_path / "artifacts" / "summaries").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.mark.integration
def test_manual_pipeline_filters_manual_only(temp_env_with_files):
    # Create context with source_filter="manual"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "manual", "project_root": str(temp_env_with_files)}
    )

    # Run bronze_raw_links with manual filter
    links = bronze_raw_links(context)

    # Should only have manual links (returns plain list of URLs)
    assert len(links) == 2
    assert all("manual" in link for link in links)
    assert all(isinstance(link, str) for link in links)


@pytest.mark.integration
def test_monitoring_pipeline_filters_monitoring_only(temp_env_with_files):
    # Create context with source_filter="monitoring"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "monitoring", "project_root": str(temp_env_with_files)}
    )

    # Run bronze_raw_links with monitoring filter
    links = bronze_raw_links(context)

    # Should only have monitoring links (returns plain list of URLs)
    assert len(links) == 2
    assert all("monitoring" in link for link in links)
    assert all(isinstance(link, str) for link in links)


@pytest.mark.integration
def test_both_filter_processes_all_links(temp_env_with_files):
    # Create context with source_filter="both"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "both", "project_root": str(temp_env_with_files)}
    )

    # Run bronze_raw_links with both filter
    links = bronze_raw_links(context)

    # Should have all links (returns plain list of URLs)
    assert len(links) == 4
    assert all(isinstance(link, str) for link in links)

    manual_links = [link for link in links if "manual" in link]
    monitoring_links = [link for link in links if "monitoring" in link]

    assert len(manual_links) == 2
    assert len(monitoring_links) == 2


@pytest.mark.integration
def test_default_filter_is_both(temp_env_with_files):
    # Create context without source_filter (should default to "both")
    context = build_asset_context()
    type(context).op_config = PropertyMock(return_value={"project_root": str(temp_env_with_files)})

    # Run bronze_raw_links
    links = bronze_raw_links(context)

    # Should have all links (default is "both")
    assert len(links) == 4
    assert all(isinstance(link, str) for link in links)
