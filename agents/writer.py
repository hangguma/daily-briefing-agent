"""
Writer Agent — 브리핑 작성 담당.

단일 책임: 선별된 기사를 요약하고 마크다운 브리핑으로 작성한다.
입력: 점수 정렬된 기사 목록  →  출력: 마크다운 브리핑
"""

from crewai import Agent, LLM

from config import settings


def build_writer() -> Agent:
    """Writer 에이전트를 생성해 반환."""
    return Agent(
        role="뉴스 브리핑 작가",
        goal=(
            "선별된 기사를 키워드별 섹션으로 묶고, 각 기사를 3줄 이내로 "
            "요약하여 읽기 좋은 마크다운 브리핑을 작성한다."
        ),
        backstory=(
            "당신은 바쁜 사람들을 위해 핵심만 전달하는 뉴스레터 작가입니다. "
            "복잡한 기사를 누구나 30초 안에 이해할 수 있도록 간결하게 "
            "요약하며, 출처 링크를 항상 함께 제공합니다. 과장이나 추측 없이 "
            "사실에 기반해 작성합니다."
        ),
        llm=LLM(model=settings.LLM_MODEL),
        verbose=True,
        max_iter=3,        # 비용 가드레일: 추론/도구 호출 반복 상한
        allow_delegation=False,
    )
