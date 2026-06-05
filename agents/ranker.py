"""
Ranker Agent — 기사 평가 담당.

단일 책임: 수집된 기사의 중복을 제거하고 중요도 점수를 매긴다.
입력: 원문 기사 목록  →  출력: 점수 정렬된 상위 기사 목록
"""

from crewai import Agent, LLM

from config import settings


def build_ranker() -> Agent:
    """Ranker 에이전트를 생성해 반환."""
    return Agent(
        role="뉴스 큐레이션 분석가",
        goal=(
            f"수집된 기사들 중 내용이 거의 같은 중복 기사를 제거하고, "
            f"신선도와 관련도를 기준으로 중요도를 평가해 "
            f"상위 {settings.TOP_N_ARTICLES}건을 선별한다."
        ),
        backstory=(
            "당신은 매일 수백 건의 기사를 검토하는 뉴스 에디터입니다. "
            "비슷한 사건을 다룬 중복 기사를 빠르게 골라내고, 독자에게 "
            "가장 가치 있는 기사를 선별하는 안목을 가지고 있습니다. "
            "각 기사가 왜 중요한지 간단한 근거와 함께 0~1 점수를 부여합니다."
        ),
        # Ranker는 외부 도구가 필요 없음 — LLM의 판단력만 사용
        llm=LLM(model=settings.LLM_MODEL),
        verbose=True,
        max_iter=3,        # 비용 가드레일: 추론/도구 호출 반복 상한
        allow_delegation=False,
    )
