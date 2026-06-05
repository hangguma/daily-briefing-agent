"""
Crew 조립 — 에이전트 시스템의 본체.

왜 이 파일을 main.py와 분리하나요?
- crew.py는 "에이전트 시스템 그 자체", main.py는 "그것을 실행하는 방법"입니다.
- Phase 2에서 main.py를 app.py(Streamlit)로 교체할 때, 이 파일은
  그대로 import해서 재사용합니다. 즉 에이전트 로직은 건드리지 않습니다.
  (Stage 3에서 약속한 설계 원칙)
"""

from crewai import Crew, Process

from agents.collector import build_collector
from agents.ranker import build_ranker
from agents.writer import build_writer
from tasks.tasks import build_collect_task, build_rank_task, build_write_task


def build_crew(keywords: list[str]) -> Crew:
    """주어진 키워드로 동작하는 브리핑 Crew를 조립해 반환.

    Args:
        keywords: 브리핑 대상 키워드 리스트

    Returns:
        실행 준비된 Crew 객체 (.kickoff()로 실행)
    """
    # 1) 에이전트 3명 생성
    collector = build_collector()
    ranker = build_ranker()
    writer = build_writer()

    # 2) 각 작업을 정의하고 context로 연결 (수집 → 평가 → 작성)
    collect_task = build_collect_task(collector, keywords)
    rank_task = build_rank_task(ranker, collect_task)
    write_task = build_write_task(writer, rank_task, keywords)

    # 3) Crew로 묶기 — sequential = 위에서 아래로 순차 실행
    return Crew(
        agents=[collector, ranker, writer],
        tasks=[collect_task, rank_task, write_task],
        process=Process.sequential,
        verbose=True,  # 관찰 가능성: 전체 실행 과정 로그 출력
    )
