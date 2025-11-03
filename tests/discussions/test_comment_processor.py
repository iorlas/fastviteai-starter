from datetime import UTC, datetime

import pytest

from dagster_project.core.discussions.comment_processor import CommentProcessor
from dagster_project.core.discussions.models import CleanedComment, HNComment


@pytest.mark.integration
def test_flatten_comments_single_level():
    comments = [
        HNComment(
            id=1,
            author="user1",
            text="First comment",
            story_id=100,
            created_at=datetime.now(UTC),
            created_at_i=1234567890,
            children=[],
        ),
        HNComment(
            id=2,
            author="user2",
            text="Second comment",
            story_id=100,
            created_at=datetime.now(UTC),
            created_at_i=1234567891,
            children=[],
        ),
    ]

    processor = CommentProcessor()
    flattened = processor.flatten_comments(comments, story_id=100)

    assert len(flattened) == 2
    assert flattened[0].comment_id == 1
    assert flattened[0].depth == 0
    assert flattened[0].thread_position == 0
    assert flattened[1].comment_id == 2
    assert flattened[1].depth == 0
    assert flattened[1].thread_position == 1


@pytest.mark.integration
def test_flatten_comments_nested():
    comments = [
        HNComment(
            id=1,
            author="user1",
            text="Parent comment",
            story_id=100,
            created_at=datetime.now(UTC),
            created_at_i=1234567890,
            children=[
                HNComment(
                    id=2,
                    author="user2",
                    text="Child comment",
                    story_id=100,
                    parent_id=1,
                    created_at=datetime.now(UTC),
                    created_at_i=1234567891,
                    children=[],
                ),
            ],
        ),
    ]

    processor = CommentProcessor()
    flattened = processor.flatten_comments(comments, story_id=100)

    assert len(flattened) == 2
    assert flattened[0].comment_id == 1
    assert flattened[0].depth == 0
    assert flattened[1].comment_id == 2
    assert flattened[1].depth == 1
    assert flattened[1].parent_id == 1


@pytest.mark.integration
def test_strip_html():
    processor = CommentProcessor()

    html = "<p>This is a <b>bold</b> statement.</p><br/>New line here."
    clean = processor._strip_html(html)

    assert "<p>" not in clean
    assert "<b>" not in clean
    assert "<br/>" not in clean
    assert "bold" in clean
    assert "statement" in clean


@pytest.mark.integration
def test_calculate_comment_quality_score():
    processor = CommentProcessor()

    comment = CleanedComment(
        comment_id=1,
        story_id=100,
        author="user1",
        text="A" * 500,
        text_html="<p>" + "A" * 500 + "</p>",
        points=50,
        created_at=datetime.now(UTC),
        created_at_i=1234567890,
        parent_id=None,
        depth=0,
        thread_position=0,
    )

    score = processor.calculate_comment_quality_score(comment)

    assert score > 0
    assert isinstance(score, float)


@pytest.mark.integration
def test_filter_high_quality():
    processor = CommentProcessor()

    comments = [
        CleanedComment(
            comment_id=1,
            story_id=100,
            author="user1",
            text="A" * 500,
            text_html=None,
            points=50,
            created_at=datetime.now(UTC),
            created_at_i=1234567890,
            parent_id=None,
            depth=0,
            thread_position=0,
        ),
        CleanedComment(
            comment_id=2,
            story_id=100,
            author="user2",
            text="Short",
            text_html=None,
            points=1,
            created_at=datetime.now(UTC),
            created_at_i=1234567891,
            parent_id=None,
            depth=3,
            thread_position=0,
        ),
    ]

    high_quality = processor.filter_high_quality(comments, min_score=3.0)

    assert len(high_quality) >= 1
    assert high_quality[0].comment_id == 1
