import re
from html import unescape

from dagster_project.core.discussions.models import CleanedComment, HNComment


class CommentProcessor:
    @staticmethod
    def flatten_comments(comments: list[HNComment], story_id: int, depth: int = 0) -> list[CleanedComment]:
        flattened = []
        for position, comment in enumerate(comments):
            if comment.text:
                cleaned = CommentProcessor._clean_comment(comment, story_id, depth, position)
                flattened.append(cleaned)

            if comment.children:
                flattened.extend(CommentProcessor.flatten_comments(comment.children, story_id, depth + 1))

        return flattened

    @staticmethod
    def _clean_comment(comment: HNComment, story_id: int, depth: int, position: int) -> CleanedComment:
        text_html = comment.text
        text_clean = CommentProcessor._strip_html(comment.text) if comment.text else ""

        return CleanedComment(
            comment_id=comment.id,
            story_id=story_id,
            author=comment.author,
            text=text_clean,
            text_html=text_html,
            points=comment.points,
            created_at=comment.created_at,
            created_at_i=comment.created_at_i,
            parent_id=comment.parent_id,
            depth=depth,
            thread_position=position,
        )

    @staticmethod
    def _strip_html(html_text: str) -> str:
        html_text = unescape(html_text)

        html_text = re.sub(r"<p>", "\n\n", html_text)
        html_text = re.sub(r"<br\s*/?>", "\n", html_text)

        html_text = re.sub(r"<[^>]+>", "", html_text)

        html_text = re.sub(r"\n{3,}", "\n\n", html_text)
        html_text = html_text.strip()

        return html_text

    @staticmethod
    def calculate_comment_quality_score(comment: CleanedComment) -> float:
        score = 0.0

        if comment.points is not None and comment.points > 0:
            score += min(comment.points / 10.0, 5.0)

        if len(comment.text) > 100:
            score += 1.0
        if len(comment.text) > 300:
            score += 1.0

        if comment.depth == 0:
            score += 2.0
        elif comment.depth == 1:
            score += 1.0

        return score

    @staticmethod
    def filter_high_quality(comments: list[CleanedComment], min_score: float = 3.0) -> list[CleanedComment]:
        scored = [(CommentProcessor.calculate_comment_quality_score(c), c) for c in comments]
        return [c for score, c in scored if score >= min_score]
