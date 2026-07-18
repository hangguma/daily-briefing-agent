"""
Writer Agent - writes the briefing.

Single responsibility: summarize selected articles into a Markdown briefing.
Input: scored article list  ->  Output: Markdown briefing
"""

from crewai import Agent, LLM

from config import settings


def build_writer() -> Agent:
    """Create and return the Writer agent."""
    return Agent(
        role="News briefing writer",
        goal=(
            "Group selected articles into per-keyword sections, summarize each "
            "article in three lines or fewer, and produce a readable Markdown "
            "briefing."
        ),
        backstory=(
            "You are a newsletter writer who delivers only the essentials for "
            "busy people. You distill complex articles so anyone can grasp them "
            "in 30 seconds, always including the source link. You write based on "
            "facts, without exaggeration or speculation."
        ),
        llm=LLM(model=settings.LLM_MODEL, max_tokens=settings.LLM_MAX_TOKENS),
        verbose=True,
        max_iter=3,        # cost guardrail: cap reasoning/tool-call loops
        allow_delegation=False,
    )
