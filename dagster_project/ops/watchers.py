"""Watcher protocol and implementations for monitoring content sources.

Watchers are pluggable components that discover new links from various sources
(RSS feeds, Reddit, Twitter, Hacker News, etc.). They implement a simple protocol
with a single method: fetch_links().

This architecture allows easy extension to support new content sources without
modifying the core pipeline logic.
"""

from typing import Protocol

import feedparser


class Watcher(Protocol):
    """Protocol for content source watchers.

    Watchers discover new links from monitored sources like RSS feeds, social media,
    or news aggregators. Each watcher implementation should handle its specific
    source type and return a list of discovered URLs.

    Example:
        class RSSWatcher:
            def fetch_links(self, source_url: str) -> list[str]:
                # Parse RSS feed and extract article URLs
                return ["https://example.com/article1", ...]
    """

    def fetch_links(self, source_url: str) -> list[str]:
        """Extract links from a monitored source.

        Args:
            source_url: The URL of the source to monitor (e.g., RSS feed URL)

        Returns:
            List of discovered article/content URLs

        Raises:
            May raise exceptions for network errors, parsing failures, etc.
            Callers should handle exceptions appropriately.
        """
        ...


class RSSWatcherError(Exception):
    """Error during RSS feed processing."""

    pass


class RSSWatcher:
    """Watcher implementation for RSS feeds.

    Uses feedparser to parse RSS/Atom feeds and extract article URLs.
    Handles malformed feeds gracefully and provides clear error messages.

    Example:
        watcher = RSSWatcher()
        links = watcher.fetch_links("https://blog.example.com/feed")
        # Returns: ["https://blog.example.com/post1", "https://blog.example.com/post2", ...]
    """

    def fetch_links(self, source_url: str) -> list[str]:
        """Extract article URLs from an RSS feed.

        Parses the RSS feed and extracts the 'link' field from each entry.
        Skips entries without valid links and handles feed parsing errors.

        Args:
            source_url: URL of the RSS feed to parse

        Returns:
            List of article URLs found in the feed (may be empty)

        Raises:
            RSSWatcherError: If feed cannot be fetched or parsed
        """
        try:
            # Parse RSS feed
            feed = feedparser.parse(source_url)

            # Check for feed parsing errors
            if feed.bozo:
                # Bozo flag indicates feed is malformed, but feedparser may still extract data
                # Log but continue processing if entries are available
                if not feed.entries:
                    raise RSSWatcherError(
                        f"Malformed RSS feed with no entries: {source_url}"
                        f" (error: {feed.get('bozo_exception', 'unknown')})"
                    )

            # Extract links from feed entries
            links = []
            for entry in feed.entries:
                # Try common link fields (RSS and Atom have different conventions)
                link = entry.get("link") or entry.get("href")
                if link:
                    links.append(link)

            return links

        except Exception as e:
            # Wrap unexpected errors in RSSWatcherError
            if isinstance(e, RSSWatcherError):
                raise
            raise RSSWatcherError(f"Error fetching RSS feed {source_url}: {e}") from e
