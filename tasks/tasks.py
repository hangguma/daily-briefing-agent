"""
Task definitions for each agent.

Why this design?
- Agent is "who"; Task is "what to do". Keeping them separate lets the same
  agent be reused for different tasks.
- context=[previous_task] passes the prior result as the next task's input.
- [Review #1 fix] Every Task sets output_pydantic to enforce the I/O contract.
- [Review #2 fix] The date can't be guessed by the LLM, so code injects it.
"""

from datetime import date

from crewai import Agent, Task

from config import settings
from models.schemas import ArticleList, BriefingReport, RankedArticleList


def build_collect_task(agent: Agent, keywords: list[str]) -> Task:
    keyword_list = ", ".join(keywords)
    return Task(
        description=(
            f"Collect the latest news for these keywords: [{keyword_list}]\n"
            f"Use BOTH tools:\n"
            f"1) news_search - pass the full keyword list (web search)\n"
            f"2) rss_fetch - pass the full keyword list (media subscription)\n"
            f"Merge both sources and organize each article into title, url, "
            f"snippet, and keyword fields."
        ),
        expected_output=(
            "A structured list of all articles collected from both sources "
            "(search + RSS). Each article includes title, url, snippet, keyword."
        ),
        agent=agent,
        output_pydantic=ArticleList,  # enforce contract
    )


def build_rank_task(agent: Agent, collect_task: Task) -> Task:
    return Task(
        description=(
            "Review the collected article list.\n"
            "1) Remove duplicate articles covering the same event.\n"
            "2) Assign each article a score between 0 and 1 by freshness and relevance.\n"
            f"3) Keep only the top {settings.TOP_N_ARTICLES} by score."
        ),
        expected_output=(
            f"The top {settings.TOP_N_ARTICLES} articles sorted by score "
            "(highest first). Each includes title, url, snippet, keyword, score."
        ),
        agent=agent,
        context=[collect_task],
        output_pydantic=RankedArticleList,  # enforce contract
    )


def build_write_task(
    agent: Agent, rank_task: Task, keywords: list[str]
) -> Task:
    today = date.today().isoformat()  # [#2] code injects the date deterministically
    keyword_list = ", ".join(keywords)
    return Task(
        description=(
            f"Write today's news briefing from the selected articles.\n"
            f"- date field: use exactly '{today}' (do not guess).\n"
            f"- keywords field: use [{keyword_list}].\n"
            f"- markdown field: use the format below.\n\n"
            f"# News Briefing ({today})\n"
            f"## [keyword]\n"
            f"### [article title]\n"
            f"- Key summary in three lines or fewer\n"
            f"- Source: [URL]\n\n"
            f"Summarize each article in three lines or fewer and always include "
            f"the source link. Write each summary in the SAME language as its "
            f"source article: summarize English articles in English and Korean "
            f"articles in Korean. Detect the language from the article's title "
            f"and content. Use the keyword text as-is for the section header."
        ),
        expected_output=(
            "A complete briefing with date, keywords, and markdown fields. "
            "The markdown has per-keyword sections, 3-line summaries, and source links."
        ),
        agent=agent,
        context=[rank_task],
        output_pydantic=BriefingReport,  # enforce contract
    )
