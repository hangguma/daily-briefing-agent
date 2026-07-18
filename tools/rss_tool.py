"""
RSS feeds wrapped as a CrewAI tool - Phase 2 multi-source adapter.

Why this design?
- If Tavily is "keyword search", RSS is "media subscription". Combining them
  widens coverage: subscription catches what search misses.
- [Core design] Output is normalized to the same text format as Tavily, so the
  Collector treats all sources identically (adapter pattern).
- Like the Tavily tool, graceful degradation: if one feed is down, the rest
  keep being collected.
"""

from datetime import datetime, timedelta, timezone

import feedparser
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

import logging

from config import settings

log = logging.getLogger("briefing")


class RssInput(BaseModel):
    """Tool input schema - takes a list of keywords."""

    keywords: list[str] = Field(description="Keywords used for filtering")


class RssFetchTool(BaseTool):
    name: str = "rss_fetch"
    description: str = (
        "Fetches the latest articles from subscribed media RSS feeds. "
        "Returns recent articles (title, URL, summary) matching the keywords."
    )
    args_schema: type[BaseModel] = RssInput

    def _matches_keyword(self, text: str, keywords: list[str]) -> str | None:
        """Return the first keyword found in title+summary, else None."""
        lowered = text.lower()
        for kw in keywords:
            if kw.lower() in lowered:
                return kw
        return None

    def _parse_feed(self, url: str, keywords: list[str], cutoff: datetime) -> list[str]:
        """Parse a single feed. Returns empty list on failure (graceful degradation)."""
        lines: list[str] = []
        try:
            feed = feedparser.parse(url)
        except Exception as e:  # noqa: BLE001
            log.error("RSS parse failed: %s - %s", url, e)
            return lines

        for entry in feed.entries:
            # 1) Freshness filter: keep only items newer than cutoff (if dated)
            #    feedparser normalizes published_parsed to UTC, so build the
            #    datetime as UTC-aware — comparing it against local time would
            #    shift the cutoff by the UTC offset (hours of mis-filtering).
            published = entry.get("published_parsed")
            if published is not None:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue
            # (Undated feeds are kept - many serve newest-first.)

            title = entry.get("title", "")
            summary = entry.get("summary", "")

            # 2) Keyword filter (toggled by settings)
            if settings.RSS_KEYWORD_FILTER:
                matched = self._matches_keyword(f"{title} {summary}", keywords)
                if matched is None:
                    continue
            else:
                matched = keywords[0] if keywords else "general"

            lines.append(
                f"- title: {title}\n"
                f"  url: {entry.get('link', '')}\n"
                f"  content: {summary[:300]}\n"
                f"  matched keyword: {matched}"
            )
        return lines

    def _run(self, keywords: list[str]) -> str:
        """Iterate over all RSS feeds and collect."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.SEARCH_DAYS)
        all_lines: list[str] = []

        for url in settings.RSS_FEEDS:
            feed_lines = self._parse_feed(url, keywords, cutoff)
            all_lines.extend(feed_lines)

        if not all_lines:
            return "[RSS] No recent articles matched the keywords."
        header = f"[RSS] {len(all_lines)} articles collected:"
        return header + "\n" + "\n".join(all_lines)
