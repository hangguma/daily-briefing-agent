"""
에이전트 사이를 흐르는 데이터 모델 (I/O 계약).

왜 이렇게 하나요?
- [Review #1 수정] 이전에는 모델을 정의만 하고 실제 파이프라인에서 쓰지
  않아 "죽은 코드"였습니다. 이제 각 Task의 output_pydantic으로 연결해
  계약을 "강제"합니다. 잘못된 형식의 데이터가 다음 단계로 넘어가는 것을
  실행 시점에 막아줍니다.
- CrewAI의 output_pydantic은 단일 모델만 받으므로, 리스트를 담을 때는
  래퍼 모델(ArticleList 등)을 사용합니다.
"""

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Collector가 수집한 원문 기사 1건."""

    title: str = Field(description="기사 제목")
    url: str = Field(description="기사 원문 URL")
    snippet: str = Field(description="본문 요약 스니펫")
    keyword: str = Field(description="이 기사를 찾아낸 검색 키워드")


class ArticleList(BaseModel):
    """Collector 작업의 출력 — 기사 목록 래퍼."""

    articles: list[Article]


class RankedArticle(Article):
    """Ranker가 점수를 매긴 기사. Article을 상속해 필드를 재사용."""

    score: float = Field(ge=0.0, le=1.0, description="중요도 점수 (0~1)")


class RankedArticleList(BaseModel):
    """Ranker 작업의 출력 — 점수 정렬된 기사 목록 래퍼."""

    articles: list[RankedArticle]


class BriefingReport(BaseModel):
    """Writer가 생성하는 최종 브리핑 리포트."""

    date: str = Field(description="생성 날짜 (YYYY-MM-DD)")
    keywords: list[str] = Field(description="브리핑 대상 키워드 목록")
    markdown: str = Field(description="마크다운 형식의 최종 브리핑 본문")
