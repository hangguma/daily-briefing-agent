"""
Ranker Agent - evaluates articles.

Single responsibility: dedupe collected articles and assign importance scores.
Input: raw article list  ->  Output: top-N scored articles
"""

from crewai import Agent, LLM

from config import settings


def build_ranker() -> Agent:
    """Create and return the Ranker agent."""
    return Agent(
        role="News curation analyst",
        goal=(
            f"Remove near-duplicate articles from the collected set, evaluate "
            f"importance by freshness and relevance, and select the top "
            f"{settings.TOP_N_ARTICLES}."
        ),
        backstory=(
            "You are a news editor who reviews hundreds of articles daily. "
            "You quickly spot duplicate articles covering the same event and "
            "have an eye for selecting the most valuable ones for the reader. "
            "You assign a 0-1 score with a brief rationale for each article."
        ),
        # The Ranker needs no external tool - it uses the LLM's judgment only.
        llm=LLM(model=settings.LLM_MODEL, max_tokens=settings.LLM_MAX_TOKENS),
        verbose=True,
        max_iter=3,        # cost guardrail: cap reasoning/tool-call loops
        allow_delegation=False,
    )
