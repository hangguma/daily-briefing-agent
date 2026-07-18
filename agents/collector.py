"""
Collector Agent - collects news.

Single responsibility: search and collect news by keyword.
Input: keyword list  ->  Output: raw article list

Phase 2: same role, expanded tools (Tavily + RSS = multi-source).
"""

from crewai import Agent, LLM

from config import settings
from tools.rss_tool import RssFetchTool
from tools.search_tool import NewsSearchTool


def build_collector() -> Agent:
    """Create and return the Collector agent."""
    return Agent(
        role="News collection specialist",
        goal=(
            "For each given keyword, use both news_search (web search) and "
            "rss_fetch (media subscription) to collect the latest news articles "
            "without omission."
        ),
        backstory=(
            "You are a researcher specialized in information gathering. You use "
            "both keyword search (Tavily) and trusted-media subscriptions (RSS) "
            "to collect articles broadly, recording title, URL, and content "
            "accurately. You never guess - you use only what the tools return."
        ),
        # Phase 2: equip both source tools (adapter pattern)
        tools=[NewsSearchTool(), RssFetchTool()],
        llm=LLM(model=settings.LLM_MODEL, max_tokens=settings.LLM_MAX_TOKENS),
        verbose=True,        # observability: log each step
        max_iter=4,          # cost guardrail (raised by 1 for the 2nd source)
        allow_delegation=False,
    )
