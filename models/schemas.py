"""
Data models passed between agents (I/O contracts).

Why this design?
- [Review #1 fix] Previously these models were defined but never used in the
  actual pipeline ("dead code"). Now each Task wires them via output_pydantic,
  turning the contract from documentation into enforcement. Malformed data is
  blocked from passing downstream at runtime.
- CrewAI's output_pydantic accepts only a single model, so lists are wrapped
  in wrapper models (ArticleList, etc.).
"""

from pydantic import BaseModel, Field


class Article(BaseModel):
    """A single raw article collected by the Collector."""

    title: str = Field(description="Article title")
    url: str = Field(description="Article source URL")
    snippet: str = Field(description="Short summary snippet")
    keyword: str = Field(description="Keyword that surfaced this article")


class ArticleList(BaseModel):
    """Collector task output - wrapper for a list of articles."""

    articles: list[Article]


class RankedArticle(Article):
    """An article scored by the Ranker. Inherits Article fields."""

    score: float = Field(ge=0.0, le=1.0, description="Importance score (0-1)")


class RankedArticleList(BaseModel):
    """Ranker task output - wrapper for the scored article list."""

    articles: list[RankedArticle]


class BriefingReport(BaseModel):
    """Final briefing report produced by the Writer."""

    date: str = Field(description="Generation date (YYYY-MM-DD)")
    keywords: list[str] = Field(description="Keywords covered by the briefing")
    markdown: str = Field(description="Final briefing body in Markdown")
