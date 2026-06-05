"""
Collector Agent — 뉴스 수집 담당.

단일 책임: 키워드로 뉴스를 검색·수집하는 일만 한다.
입력: 키워드 리스트  →  출력: 원문 기사 목록
"""

from crewai import Agent, LLM

from config import settings
from tools.search_tool import NewsSearchTool


def build_collector() -> Agent:
    """Collector 에이전트를 생성해 반환."""
    return Agent(
        role="뉴스 수집 전문가",
        goal=(
            "주어진 각 키워드에 대해 news_search 도구를 사용하여 "
            "최신 뉴스 기사를 빠짐없이 수집한다."
        ),
        backstory=(
            "당신은 정보 수집에 특화된 리서처입니다. 주어진 키워드마다 "
            "검색 도구를 호출해 관련 기사를 모으고, 제목·URL·내용을 "
            "정확히 기록하는 데 능숙합니다. 추측하지 않고 도구가 반환한 "
            "실제 결과만 사용합니다."
        ),
        tools=[NewsSearchTool()],
        llm=LLM(model=settings.LLM_MODEL),
        verbose=True,
        max_iter=3,        # 비용 가드레일: 추론/도구 호출 반복 상한        # 관찰 가능성: 각 단계 로그 출력
        allow_delegation=False,
    )
