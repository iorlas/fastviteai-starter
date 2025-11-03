import pytest

from dagster_project.core.aggregator_resolver import resolve_url


@pytest.mark.integration
def test_resolve_url_handles_regular_urls():
    result = resolve_url("https://example.com/article")

    assert result.resolved_url == "https://example.com/article"
    assert result.original_url == "https://example.com/article"
    assert result.was_aggregator is False
    assert result.aggregator_type is None


@pytest.mark.integration
def test_resolve_url_resolves_hackernews():
    result = resolve_url("https://news.ycombinator.com/item?id=45762012")

    assert result.was_aggregator is True
    assert result.aggregator_type == "hackernews"
    assert result.resolved_url != result.original_url
    assert result.title is not None


@pytest.mark.integration
def test_resolve_url_extracts_hn_external_links():
    result = resolve_url("https://news.ycombinator.com/item?id=1")

    assert result.was_aggregator is True
    assert result.aggregator_type == "hackernews"
    assert result.resolved_url is not None
    assert result.title is not None
