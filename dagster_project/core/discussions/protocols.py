from typing import Protocol


class CommentProtocol(Protocol):
    """Protocol for platform-agnostic comment access."""

    children: list

    def count_total_comments(self) -> int:
        """Count all nested comments recursively."""
        ...
