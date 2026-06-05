"""
Tavily 웹 검색을 CrewAI 도구(Tool)로 래핑.

왜 이렇게 하나요?
- 에이전트가 "검색"이라는 능력을 쓰려면 도구로 제공해야 합니다.
- [Review #4 수정] 도구가 키워드 "리스트"를 받아 내부에서 모두 검색합니다.
  이전에는 키워드별로 에이전트가 도구를 여러 번 호출하게 했는데, 에이전트가
  일부 키워드를 빠뜨릴 위험이 있었습니다. 리스트를 한 번에 처리하면
  모든 키워드가 빠짐없이 검색됨이 보장됩니다.
- Stage 4 에러 처리 전략(재시도 + graceful degradation)을 유지합니다.
"""

import time

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tavily import TavilyClient

from config import settings


class SearchInput(BaseModel):
    """도구 입력 스키마 — 키워드 리스트를 한 번에 받음."""

    keywords: list[str] = Field(description="검색할 키워드 목록")


class NewsSearchTool(BaseTool):
    name: str = "news_search"
    description: str = (
        "여러 키워드로 최신 뉴스를 한 번에 검색합니다. "
        "각 키워드별로 제목, URL, 본문 스니펫이 담긴 기사 목록을 반환합니다."
    )
    args_schema: type[BaseModel] = SearchInput

    def _search_one(self, client: TavilyClient, keyword: str) -> str:
        """키워드 1개 검색. 실패 시 최대 3회 재시도, 최종 실패 시 빈 결과."""
        for attempt in range(1, 4):
            try:
                resp = client.search(
                    query=keyword,
                    max_results=settings.RESULTS_PER_KEYWORD,
                    topic=settings.SEARCH_TOPIC,          # 설정에서 읽음 (단일 출처)
                    search_depth=settings.SEARCH_DEPTH,   # 설정에서 읽음
                    days=settings.SEARCH_DAYS,            # 신선도: 최근 N일 이내
                )
                results = resp.get("results", [])
                lines = [f"\n[키워드: {keyword}] 검색 결과 {len(results)}건:"]
                for r in results:
                    lines.append(
                        f"- 제목: {r.get('title', '')}\n"
                        f"  URL: {r.get('url', '')}\n"
                        f"  내용: {r.get('content', '')[:300]}"
                    )
                return "\n".join(lines)

            except Exception as e:  # noqa: BLE001
                wait = 2 ** attempt
                if attempt < 3:
                    print(f"  ⚠️ '{keyword}' 검색 실패 (시도 {attempt}/3): {e}")
                    time.sleep(wait)
                else:
                    print(f"  ❌ '{keyword}' 최종 실패, 건너뜁니다: {e}")
                    return f"\n[키워드: {keyword}] 검색 실패 — 결과 없음"
        return f"\n[키워드: {keyword}] 검색 실패 — 결과 없음"

    def _run(self, keywords: list[str]) -> str:
        """모든 키워드를 순회하며 검색 — 빠짐없이 처리 보장."""
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        return "\n".join(self._search_one(client, kw) for kw in keywords)
