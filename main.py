"""
Phase 1 진입점 — 커맨드라인에서 브리핑 에이전트를 실행한다.

실행:
    python main.py
    python main.py --keywords "agentic AI" "RAG" "vector DB"

Phase 2에서는 이 파일 대신 app.py(Streamlit)가 build_crew를 호출합니다.
에이전트 로직(crew.py)은 그대로 재사용됩니다.
"""

import argparse
import os
from datetime import date, datetime

from config import settings
from crew import build_crew


def parse_args() -> list[str]:
    """CLI 인자에서 키워드를 읽음. 없으면 기본 키워드 사용."""
    parser = argparse.ArgumentParser(description="Daily Briefing Agent")
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=settings.DEFAULT_KEYWORDS,
        help="브리핑 대상 키워드 (공백으로 구분, 최대 5개 권장)",
    )
    args = parser.parse_args()
    return args.keywords[:5]  # 안전하게 최대 5개로 제한


def format_search_conditions(keywords: list[str]) -> str:
    """이 브리핑이 생성된 검색 조건을 마크다운 푸터로 만든다.

    왜 LLM이 아니라 코드가 만드나요?
    - 검색 조건은 설정값으로 "정확히 알 수 있는" 결정론적 정보입니다.
      LLM에게 맡기면 추측·환각이 생길 수 있으므로, 코드가 직접 주입해
      항상 사실과 일치하도록 합니다. (Review #2와 같은 원칙)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    keyword_str = ", ".join(f"`{k}`" for k in keywords)
    return (
        "\n\n---\n"
        "## 🔍 이 브리핑의 검색 조건\n\n"
        f"| 항목 | 값 |\n"
        f"| --- | --- |\n"
        f"| 키워드 | {keyword_str} |\n"
        f"| 키워드당 기사 수 | {settings.RESULTS_PER_KEYWORD}건 |\n"
        f"| 최종 선별 기사 수 | 상위 {settings.TOP_N_ARTICLES}건 |\n"
        f"| 검색 기간 | 최근 {settings.SEARCH_DAYS}일 이내 |\n"
        f"| 검색 카테고리 | {settings.SEARCH_TOPIC} |\n"
        f"| 검색 깊이 | {settings.SEARCH_DEPTH} |\n"
        f"| 사용 모델 | {settings.LLM_MODEL} |\n"
        f"| 생성 시각 | {now} |\n"
    )


def save_report(markdown: str) -> str:
    """마크다운 브리핑을 outputs/ 폴더에 .md 파일로 저장."""
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    today = date.today().isoformat()
    path = os.path.join(settings.OUTPUT_DIR, f"briefing_{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


def main() -> None:
    # 1) 실행 전 API 키 점검 (조기 실패)
    settings.validate()

    keywords = parse_args()
    print(f"\n🚀 브리핑 시작 — 키워드: {', '.join(keywords)}\n")

    # 2) Crew 조립 후 실행
    crew = build_crew(keywords)
    try:
        result = crew.kickoff()
    except Exception as e:  # noqa: BLE001
        # [Review #3] API 인증 실패·네트워크 오류·토큰 한도 등 런타임 예외 처리.
        # validate()는 키 "존재"만 확인하므로, 키 "유효성"은 여기서 드러납니다.
        print(f"\n❌ 브리핑 생성 중 오류가 발생했습니다: {e}")
        print("   - ANTHROPIC_API_KEY / TAVILY_API_KEY 유효성을 확인하세요.")
        print("   - 네트워크 연결과 API 사용 한도를 확인하세요.")
        return

    # 3) 결과 추출 — output_pydantic 덕분에 구조화된 객체로 받음
    #    (구버전/파싱 실패 대비해 문자열 폴백도 처리)
    report = getattr(result, "pydantic", None)
    markdown = report.markdown if report else str(result)

    # 3-1) 검색 조건 메타데이터를 코드가 직접 덧붙임 (결정론적, 사실 보장)
    markdown += format_search_conditions(keywords)

    # 4) 저장 + 콘솔 출력
    path = save_report(markdown)
    print("\n" + "=" * 50)
    print(markdown)
    print("=" * 50)
    print(f"\n✅ 브리핑 완료! → {path}")


if __name__ == "__main__":
    main()
