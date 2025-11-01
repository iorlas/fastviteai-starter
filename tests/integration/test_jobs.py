from unittest.mock import PropertyMock

import pytest
from dagster import build_asset_context

from dagster_project.assets.link_ingestion import link_ingestion_asset


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


def test_manual_pipeline_filters_manual_only(temp_env_with_files):
    # Create context with source_filter="manual"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "manual", "project_root": str(temp_env_with_files)}
    )

    # Run link ingestion with manual filter
    links = link_ingestion_asset(context)

    # Should only have manual links
    assert len(links) == 2
    assert all("manual" in link.url for link in links)
    assert all(link.source_file == "manual" for link in links)


def test_monitoring_pipeline_filters_monitoring_only(temp_env_with_files):
    # Create context with source_filter="monitoring"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "monitoring", "project_root": str(temp_env_with_files)}
    )

    # Run link ingestion with monitoring filter
    links = link_ingestion_asset(context)

    # Should only have monitoring links
    assert len(links) == 2
    assert all("monitoring" in link.url for link in links)
    assert all(link.source_file == "monitoring" for link in links)


def test_both_filter_processes_all_links(temp_env_with_files):
    # Create context with source_filter="both"
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "both", "project_root": str(temp_env_with_files)}
    )

    # Run link ingestion with both filter
    links = link_ingestion_asset(context)

    # Should have all links
    assert len(links) == 4

    manual_links = [link for link in links if link.source_file == "manual"]
    monitoring_links = [link for link in links if link.source_file == "monitoring"]

    assert len(manual_links) == 2
    assert len(monitoring_links) == 2


def test_default_filter_is_both(temp_env_with_files):
    # Create context without source_filter (should default to "both")
    context = build_asset_context()
    type(context).op_config = PropertyMock(return_value={"project_root": str(temp_env_with_files)})

    # Run link ingestion
    links = link_ingestion_asset(context)

    # Should have all links (default is "both")
    assert len(links) == 4
