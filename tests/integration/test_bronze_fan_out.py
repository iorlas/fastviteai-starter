import pytest

from dagster_project.core.content_types.youtube import YouTubeExtractor


def _detect_content_type(url: str) -> str:
    youtube_extractor = YouTubeExtractor()
    if youtube_extractor.matches(url):
        return "youtube"
    return "html"


@pytest.mark.integration
def test_discovered_urls_routing_by_type():
    test_urls = [
        {"url": "https://youtube.com/watch?v=123", "url_hash": "yt_hash_1"},
        {"url": "https://example.com/article", "url_hash": "html_hash_1"},
        {"url": "https://youtu.be/456", "url_hash": "yt_hash_2"},
        {"url": "https://news.ycombinator.com/item?id=789", "url_hash": "html_hash_2"},
    ]

    youtube_urls = [u for u in test_urls if _detect_content_type(u["url"]) == "youtube"]
    html_urls = [u for u in test_urls if _detect_content_type(u["url"]) == "html"]

    assert len(youtube_urls) == 2
    assert len(html_urls) == 2
    assert len(youtube_urls) + len(html_urls) == len(test_urls)


@pytest.mark.integration
def test_no_url_processed_by_multiple_bronze_assets():
    test_urls = [
        {"url": "https://youtube.com/watch?v=123", "url_hash": "yt_1"},
        {"url": "https://example.com", "url_hash": "html_1"},
    ]

    youtube_urls = [u for u in test_urls if _detect_content_type(u["url"]) == "youtube"]
    html_urls = [u for u in test_urls if _detect_content_type(u["url"]) == "html"]

    youtube_hashes = {u["url_hash"] for u in youtube_urls}
    html_hashes = {u["url_hash"] for u in html_urls}

    assert youtube_hashes.isdisjoint(html_hashes)


@pytest.mark.integration
def test_bronze_asset_filtering():
    all_urls = [
        {"url": "https://youtube.com/watch?v=1", "url_hash": "yt_1"},
        {"url": "https://youtube.com/watch?v=2", "url_hash": "yt_2"},
        {"url": "https://example.com/1", "url_hash": "html_1"},
        {"url": "https://example.com/2", "url_hash": "html_2"},
        {"url": "https://example.com/3", "url_hash": "html_3"},
    ]

    youtube_urls = [u for u in all_urls if _detect_content_type(u["url"]) == "youtube"]
    html_urls = [u for u in all_urls if _detect_content_type(u["url"]) == "html"]

    assert len(youtube_urls) == 2
    assert len(html_urls) == 3
    assert all(_detect_content_type(u["url"]) == "youtube" for u in youtube_urls)
    assert all(_detect_content_type(u["url"]) == "html" for u in html_urls)
