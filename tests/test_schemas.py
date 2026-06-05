"""
데이터 모델(I/O 계약) 단위 테스트.

API 호출이 전혀 없으므로 어떤 환경에서도 실행 가능합니다.
계약이 "잘못된 데이터를 실제로 거부하는지"를 검증합니다.
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


def test_article_정상_생성():
    a = Article(title="제목", url="https://x.com", snippet="요약", keyword="AI")
    assert a.title == "제목"
    assert a.keyword == "AI"


def test_article_필수필드_누락시_에러():
    # url을 빠뜨리면 검증 실패해야 함 (계약 강제)
    with pytest.raises(ValidationError):
        Article(title="제목", snippet="요약", keyword="AI")


def test_ranked_article_점수_범위_검증():
    # score는 0~1 범위. 범위를 벗어나면 거부되어야 함.
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


def test_ranked_article_는_article_상속():
    # 상속 구조 검증 — RankedArticle은 Article의 필드를 모두 가짐
    assert issubclass(RankedArticle, Article)


def test_article_list_래퍼():
    lst = ArticleList(
        articles=[
            Article(title="t1", url="https://a.com", snippet="s", keyword="k"),
            Article(title="t2", url="https://b.com", snippet="s", keyword="k"),
        ]
    )
    assert len(lst.articles) == 2


def test_ranked_list_래퍼():
    lst = RankedArticleList(
        articles=[
            RankedArticle(
                title="t", url="https://a.com", snippet="s",
                keyword="k", score=0.9,
            )
        ]
    )
    assert lst.articles[0].score == 0.9


def test_briefing_report_정상_생성():
    report = BriefingReport(
        date="2026-06-04",
        keywords=["AI", "agents"],
        markdown="# 브리핑\n내용",
    )
    assert report.date == "2026-06-04"
    assert "브리핑" in report.markdown
