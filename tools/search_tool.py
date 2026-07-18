"""
Tavily web search wrapped as a CrewAI tool.

Why this design?
- An agent needs a tool to use a "search" capability.
- [Review #4 fix] The tool accepts a LIST of keywords and searches them all
  internally. Previously the agent called the tool once per keyword and could
  skip some; processing the list in one call guarantees every keyword is searched.
- Keeps the error-handling strategy: retry + graceful degradation.
"""

import time

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tavily import TavilyClient

import logging

from config import settings

log = logging.getLogger("briefing")


class SearchInput(BaseModel):
    """Tool input schema - takes a list of keywords at once."""

    keywords: list[str] = Field(description="Keywords to search")


class NewsSearchTool(BaseTool):
    name: str = "news_search"
    description: str = (
        "Searches the latest news for several keywords at once. "
        "Returns, per keyword, a list of articles with title, URL, and snippet."
    )
    args_schema: type[BaseModel] = SearchInput

    def _search_one(self, client: TavilyClient, keyword: str) -> str:
        """Search a single keyword. Retry up to 3 times, empty result on final failure."""
        for attempt in range(1, 4):
            try:
                resp = client.search(
                    query=keyword,
                    max_results=settings.RESULTS_PER_KEYWORD,
                    topic=settings.SEARCH_TOPIC,          # from settings (single source of truth)
                    search_depth=settings.SEARCH_DEPTH,   # from settings
                    days=settings.SEARCH_DAYS,            # freshness: within last N days
                )
                results = resp.get("results", [])
                lines = [f"\n[keyword: {keyword}] {len(results)} results:"]
                for r in results:
                    lines.append(
                        f"- title: {r.get('title', '')}\n"
                        f"  url: {r.get('url', '')}\n"
                        f"  content: {r.get('content', '')[:300]}"
                    )
                return "\n".join(lines)

            except Exception as e:  # noqa: BLE001
                wait = 2 ** attempt
                if attempt < 3:
                    log.warning("search failed for '%s' (attempt %d/3): %s", keyword, attempt, e)
                    time.sleep(wait)
                else:
                    log.error("'%s' failed permanently, skipping: %s", keyword, e)
                    return f"\n[keyword: {keyword}] search failed - no results"
        return f"\n[keyword: {keyword}] search failed - no results"

    def _run(self, keywords: list[str]) -> str:
        """Iterate over all keywords - guarantees none are skipped."""
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        return "\n".join(self._search_one(client, kw) for kw in keywords)
