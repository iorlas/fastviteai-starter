"""Progress bar utilities for pipeline stages."""

from collections.abc import Iterable, Iterator
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn


class ProgressIterator:
    """Iterator wrapper with progress bar."""

    def __init__(self, items: Iterable[Any], description: str) -> None:
        self.items_list = list(items)
        self.description = description
        self.console = Console()
        self.prog: Progress | None = None
        self.task_id = None
        self._index = 0

    def __enter__(self) -> "ProgressIterator":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def __iter__(self) -> Iterator[Any]:
        self._index = 0
        self.prog = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )
        self.prog.__enter__()
        self.task_id = self.prog.add_task(self.description, total=len(self.items_list))
        return self

    def __next__(self) -> Any:
        if self._index >= len(self.items_list):
            if self.prog:
                self.prog.__exit__(None, None, None)
            raise StopIteration

        item = self.items_list[self._index]
        self._index += 1

        if self.prog and self.task_id is not None:
            self.prog.advance(self.task_id, advance=1)

        return item


def progress(items: Iterable, description: str) -> ProgressIterator:
    """Create progress bar wrapper for iterating over items.

    Args:
        items: Iterable to process
        description: Progress bar description

    Returns:
        ProgressIterator that can be used in for loops

    Example:
        for url in progress(urls, "Processing..."):
            process(url)
    """
    return ProgressIterator(items, description)
