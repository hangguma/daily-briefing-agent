# 📰 Daily Briefing Agent

키워드 기반으로 매일의 뉴스를 **자동 수집 → 선별 → 요약**해주는 멀티에이전트 시스템입니다.
[CrewAI](https://crewai.com)로 구축한 3-에이전트 순차 파이프라인입니다.

## 🎯 무엇을 하나요?

```
관심 키워드 입력  →  뉴스 자동 수집  →  중복 제거·중요도 평가  →  마크다운 브리핑 생성
```

세 개의 전문화된 에이전트가 협업합니다:

| 에이전트 | 역할 | 도구 |
|---|---|---|
| **Collector** | 키워드로 최신 뉴스 검색·수집 | Tavily Search |
| **Ranker** | 중복 제거 + 중요도 점수화 | (LLM 판단) |
| **Writer** | 3줄 요약 + 마크다운 브리핑 작성 | (LLM 작성) |

## 🏗️ 아키텍처

```
사용자 키워드
    ↓
[Collector] ──(Tavily)──> 원문 기사 목록
    ↓
[Ranker] ──────────────> 점수 정렬 상위 N건
    ↓
[Writer] ──(Claude)────> 마크다운 브리핑 (.md)
```

설계 원칙: **단일 책임** · **명확한 I/O 계약(Pydantic)** · **관찰 가능성(verbose)** · **graceful degradation(검색 실패 시 재시도)**

## 🚀 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. API 키 설정
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY, TAVILY_API_KEY 입력

# 3. 실행
python main.py

# 또는 직접 키워드 지정
python main.py --keywords "agentic AI" "RAG" "vector database"
```

결과는 `outputs/briefing_YYYY-MM-DD.md`에 저장됩니다.

## 📁 프로젝트 구조

```
daily-briefing-agent/
├── agents/        # 에이전트 정의 (역할·목표·백스토리)
├── tasks/         # 작업 정의 (무엇을 할지)
├── tools/         # 외부 도구 래퍼 (Tavily 검색)
├── models/        # 데이터 모델 (Pydantic 스키마)
├── config/        # 설정·환경변수
├── crew.py        # 에이전트 시스템 조립 (재사용 가능한 핵심)
└── main.py        # CLI 진입점
```

## 🛣️ 로드맵

- [x] **Phase 1** — 로컬 CLI 버전
- [ ] **Phase 2** — Streamlit 웹 UI (`crew.py` 재사용, `main.py` → `app.py`)
- [ ] **Phase 3** — 스케줄러(cron) + Slack/이메일 자동 발송

## 🧰 기술 선택 노트

> **CrewAI를 선택한 이유**: 역할 기반 멀티에이전트 협업에 직관적이고
> 빠른 프로토타이핑에 최적. 단순 순차 워크플로우라 디버깅도 쉬움.
> 향후 프로덕션급 상태 관리·조건 분기가 필요해지면 **LangGraph**로
> 마이그레이션 예정 (업계 표준 학습 경로).

## 📦 기술 스택

`Python` · `CrewAI` · `Claude API` · `Tavily` · `Pydantic`

## 👤 Author

**[Eunjin Cho]**

- GitHub: [@hangguma](https://github.com/hangguma)
- LinkedIn: [프로필 링크](https://linkedin.com/in/eunjincho)

> 이 프로젝트는 Agentic AI 학습 및 포트폴리오 목적으로 제작되었습니다.

## 📄 License

이 프로젝트는 MIT License를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

