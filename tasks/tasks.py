"""
각 에이전트가 수행할 작업(Task) 정의.

왜 이렇게 하나요?
- Agent는 "누구인가", Task는 "무엇을 하는가"를 분리합니다.
- context=[이전_task]로 연결하면 이전 결과가 다음 작업 입력으로 전달됩니다.
- [Review #1 수정] 모든 Task에 output_pydantic을 지정해 I/O 계약을 강제합니다.
- [Review #2 수정] 날짜는 LLM이 추측하지 못하므로 코드가 주입합니다.
"""

from datetime import date

from crewai import Agent, Task

from config import settings
from models.schemas import ArticleList, BriefingReport, RankedArticleList


def build_collect_task(agent: Agent, keywords: list[str]) -> Task:
    keyword_list = ", ".join(keywords)
    return Task(
        description=(
            f"news_search 도구를 호출하여 다음 키워드들의 최신 뉴스를 "
            f"한 번에 수집하세요: [{keyword_list}]\n"
            f"도구에 위 키워드 전체를 리스트로 전달하세요.\n"
            f"수집된 각 기사를 title, url, snippet, keyword 필드로 정리하세요."
        ),
        expected_output=(
            "수집된 모든 기사를 담은 구조화된 목록. 각 기사는 "
            "title, url, snippet, keyword를 포함한다."
        ),
        agent=agent,
        output_pydantic=ArticleList,  # ← 계약 강제
    )


def build_rank_task(agent: Agent, collect_task: Task) -> Task:
    return Task(
        description=(
            "수집된 기사 목록을 검토하세요.\n"
            "1) 같은 사건을 다룬 중복 기사를 제거합니다.\n"
            "2) 각 기사에 신선도와 관련도 기준으로 0~1 사이 score를 매깁니다.\n"
            f"3) score가 높은 순으로 상위 {settings.TOP_N_ARTICLES}건만 "
            f"남깁니다."
        ),
        expected_output=(
            f"score가 높은 순으로 정렬된 상위 {settings.TOP_N_ARTICLES}건의 "
            "기사 목록. 각 기사는 title, url, snippet, keyword, score를 포함한다."
        ),
        agent=agent,
        context=[collect_task],
        output_pydantic=RankedArticleList,  # ← 계약 강제
    )


def build_write_task(
    agent: Agent, rank_task: Task, keywords: list[str]
) -> Task:
    today = date.today().isoformat()  # [#2] 코드가 날짜를 결정론적으로 주입
    keyword_list = ", ".join(keywords)
    return Task(
        description=(
            f"선별된 기사로 오늘의 뉴스 브리핑을 작성하세요.\n"
            f"- date 필드: 반드시 '{today}'를 사용하세요 (추측 금지).\n"
            f"- keywords 필드: [{keyword_list}]를 사용하세요.\n"
            f"- markdown 필드: 아래 형식으로 작성하세요.\n\n"
            f"# 📰 오늘의 브리핑 ({today})\n"
            f"## 🔑 [키워드]\n"
            f"### [기사 제목]\n"
            f"- 3줄 이내 핵심 요약\n"
            f"- 🔗 출처: [URL]\n\n"
            f"각 기사를 3줄 이내로 요약하고 출처 링크를 반드시 포함하세요. "
            f"한국어로 작성합니다."
        ),
        expected_output=(
            "date, keywords, markdown 필드를 가진 완성된 브리핑. "
            "markdown은 키워드별 섹션과 3줄 요약, 출처 링크를 포함한다."
        ),
        agent=agent,
        context=[rank_task],
        output_pydantic=BriefingReport,  # ← 계약 강제
    )
