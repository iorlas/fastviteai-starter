from typing import Protocol

import feedparser


class Watcher(Protocol):
    def fetch_links(self, source_url: str) -> list[str]: ...


class RSSWatcherError(Exception):
    pass


class RSSWatcher:
    def fetch_links(self, source_url: str) -> list[str]:
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
