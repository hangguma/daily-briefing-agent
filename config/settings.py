"""
프로젝트 전역 설정.

왜 이렇게 하나요?
- API 키를 코드에 하드코딩하면 git에 올릴 때 유출됩니다.
  .env 파일로 분리하고 os.getenv로 읽어옵니다. (Stage 3 수용 기준)
- 키워드/모델명 같은 "바뀔 수 있는 값"을 한 곳에 모아두면,
  나중에 Streamlit(Phase 2)에서 이 값들만 동적으로 주입하면 됩니다.
"""

import os

from dotenv import load_dotenv

# .env 파일을 읽어 환경변수로 로드
load_dotenv()

# ── API 키 ───────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# ── LLM 설정 ─────────────────────────────────────────────
# CrewAI는 내부적으로 LiteLLM을 사용하므로 "anthropic/모델명" 형식을 씁니다.
LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")

# ── 파이프라인 파라미터 ────────────────────────────────────
# Phase 2에서는 이 값들을 UI 입력으로 대체합니다.
DEFAULT_KEYWORDS: list[str] = ["agentic AI", "LLM 에이전트", "AI 스타트업 투자"]
RESULTS_PER_KEYWORD: int = 5   # 키워드당 검색 기사 수
TOP_N_ARTICLES: int = 6        # 최종 브리핑에 포함할 상위 기사 수
SEARCH_DAYS: int = 7           # 최근 N일 이내 뉴스만 검색 (신선도)
SEARCH_TOPIC: str = "news"     # Tavily 검색 카테고리 (news / general)
SEARCH_DEPTH: str = "basic"    # 검색 깊이 (basic=저비용 / advanced=고품질)

# ── 출력 설정 ─────────────────────────────────────────────
OUTPUT_DIR: str = "outputs"


def validate() -> None:
    """필수 API 키가 설정됐는지 실행 전에 점검."""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    if missing:
        raise ValueError(
            f"환경변수가 없습니다: {', '.join(missing)}\n"
            f".env.example을 복사해 .env를 만들고 키를 채워주세요."
        )
