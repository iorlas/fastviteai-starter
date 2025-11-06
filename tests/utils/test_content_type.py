import pytest

from dagster_project.utils.content_type import ContentType, detect_content_type


@pytest.mark.parametrize(
    "url,expected_type",
    [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", ContentType.YOUTUBE),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", ContentType.YOUTUBE),
        ("https://youtu.be/dQw4w9WgXcQ", ContentType.YOUTUBE),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", ContentType.YOUTUBE),
        ("https://example.com/article", ContentType.HTML),
        ("https://news.ycombinator.com/item?id=123", ContentType.HTML),
        ("https://github.com/owner/repo", ContentType.HTML),
        ("https://twitter.com/user/status/123", ContentType.HTML),
    ],
)
def test_detect_content_type(url: str, expected_type: ContentType):
    assert detect_content_type(url) == expected_type


def test_detect_content_type_case_insensitive():
    assert detect_content_type("https://YouTube.COM/watch?v=123") == ContentType.YOUTUBE
    assert detect_content_type("https://YOUTU.BE/123") == ContentType.YOUTUBE


def test_detect_content_type_default_html():
    assert detect_content_type("https://unknown-domain.xyz/page") == ContentType.HTML
