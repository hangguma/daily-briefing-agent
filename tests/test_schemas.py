"""
Unit tests for the data models (I/O contracts).

No API calls, so these run in any environment.
They verify the contracts actually REJECT invalid data.
"""

import pytest
from pydantic import ValidationError

from models.schemas import (
    Article,
    ArticleList,
    BriefingReport,
    RankedArticle,
    RankedArticleList,
)


def test_article_creates_ok():
    a = Article(title="Title", url="https://x.com", snippet="summary", keyword="AI")
    assert a.title == "Title"
    assert a.keyword == "AI"


def test_article_missing_required_field_errors():
    # Omitting url must fail validation (contract enforcement)
    with pytest.raises(ValidationError):
        Article(title="Title", snippet="summary", keyword="AI")


def test_ranked_article_score_range():
    # score must be within 0-1; out-of-range must be rejected
    ok = RankedArticle(
        title="t", url="https://x.com", snippet="s", keyword="k", score=0.8
    )
    assert ok.score == 0.8

    with pytest.raises(ValidationError):
        RankedArticle(
            title="t", url="https://x.com", snippet="s", keyword="k", score=1.5
        )
    with pytest.raises(ValidationError):
        RankedArticle(
            title="t", url="https://x.com", snippet="s", keyword="k", score=-0.1
        )


def test_ranked_article_inherits_article():
    # Inheritance check - RankedArticle has all Article fields
    assert issubclass(RankedArticle, Article)


def test_article_list_wrapper():
    lst = ArticleList(
        articles=[
            Article(title="t1", url="https://a.com", snippet="s", keyword="k"),
            Article(title="t2", url="https://b.com", snippet="s", keyword="k"),
        ]
    )
    assert len(lst.articles) == 2


def test_ranked_list_wrapper():
    lst = RankedArticleList(
        articles=[
            RankedArticle(
                title="t", url="https://a.com", snippet="s",
                keyword="k", score=0.9,
            )
        ]
    )
    assert lst.articles[0].score == 0.9


def test_briefing_report_creates_ok():
    report = BriefingReport(
        date="2026-06-04",
        keywords=["AI", "agents"],
        markdown="# Briefing\nbody",
    )
    assert report.date == "2026-06-04"
    assert "Briefing" in report.markdown
