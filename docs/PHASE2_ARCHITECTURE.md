# 🏛️ Phase 2 — Architecture Decision Record

> Daily Briefing Agent을 "수동 도구"에서 "스스로 도는 자율 에이전트"로 확장하는 Phase 2의 아키텍처 결정 기록.

---

## Goal

```
Daily schedule  →  Multi-keyword + multi-source search  →  Slack auto-delivery
hosted on AWS (serverless)  +  Streamlit web UI for on-demand runs
```

---

## Architecture Overview

```
[Automation path]
  EventBridge (America/Los_Angeles, daily 8am)
      ↓
  AWS Lambda (container image, env-var secrets)
      ↓
  crew.py → Collector(Tavily + RSS) → Ranker → Writer → Slack Notifier
      ↓
  Slack channel (received daily)

[On-demand path]
  Streamlit Community Cloud → reuses the same crew.py

[Reserved for later]
  X (Twitter) source adapter · Email notifier
```

**Key insight:** The Phase 1 separation of `crew.py` (logic) from execution makes this possible.
Lambda, Streamlit, and local CLI all reuse the *same* `crew.py` — only the trigger and
output adapter differ. The core logic does not change.

---

## Decisions

| # | Topic | Decision | Rationale |
|---|---|---|---|
| 1 | Packaging | **Container image** (ECR + Lambda) | crewai + deps likely exceed the 250MB zip limit; container guarantees "works locally = works on Lambda" |
| 2 | Secrets | **Lambda environment variables** | Free, sufficient for a personal project; SAM template holding them is gitignored |
| 3 | Schedule | `cron(0 8 * * ? *)` + `ScheduleExpressionTimezone: America/Los_Angeles` | Avoids UTC math and handles PST/PDT daylight-saving automatically |
| 4 | Sources | **Tavily + RSS** (X deferred) | RSS is free/stable subscription; Tavily is keyword search; both normalize to the `Article` model. X API is pay-per-use with OAuth complexity — added later via the same adapter pattern |
| 5 | Output | **Slack only** (Email deferred) | Original requirement; high alerting value; simplest setup (one webhook URL) |
| 6 | Web UI | **Streamlit Community Cloud** | Free, GitHub-linked, far simpler than self-hosting on AWS |

---

## New Modules (added on top of Phase 1)

```
daily-briefing-agent/
├── (existing) agents/ tasks/ models/ config/ crew.py
├── tools/
│   ├── search_tool.py        # existing Tavily
│   └── rss_tool.py           # NEW: RSS source adapter
├── notifiers/
│   └── slack_notifier.py     # NEW: Slack output adapter (Block Kit)
├── lambda_handler.py         # NEW: AWS Lambda entry point
├── app.py                    # NEW: Streamlit web UI
└── infra/
    └── template.yaml         # NEW: AWS SAM (Lambda + EventBridge)
```

---

## Adapter Pattern (the core design idea)

**Input adapters** — all normalize to the `Article` model so Ranker/Writer are source-agnostic:
- Tavily (keyword search)
- RSS (subscription feeds)
- X / Twitter (reserved)

**Output adapters** — all consume the same `BriefingReport`:
- File save (.md) — existing
- Slack notifier — Phase 2
- Email notifier — reserved

---

## Lambda Constraints (must design around)

| Constraint | Impact | Mitigation |
|---|---|---|
| 15-min timeout | Long crew runs get cut off | Limit keyword/source counts; set generous timeout (e.g. 600s) |
| 250MB zip limit | crewai is heavy | Use container image (up to 10GB) |
| No `.env` files | Secrets handling | Lambda environment variables |
| UTC default | Schedule drift | `ScheduleExpressionTimezone: America/Los_Angeles` |

---

## Implementation Plan (local-first)

```
1) RSS source adapter        → verify locally
2) Slack notifier adapter    → verify locally
3) Streamlit web UI          → verify locally
4) Lambda + EventBridge      → package & deploy what already works
```

**Why this order:** Steps 1–3 verify fast and free on the local machine. Step 4 (AWS) only
packages already-working code. Debugging on AWS is slow and costly, so finish as much as
possible locally before going up.

---

## Cost Estimate

| Service | Cost |
|---|---|
| EventBridge schedule | Effectively free (free tier) |
| Lambda (1 run/day, few min) | ~$0 |
| Streamlit Community Cloud | Free |
| Tavily | Free tier |
| RSS | Free |
| **Total** | **Near zero for a personal project** |

---

**Status:** Architecture confirmed. Next: implementation Step 1 (RSS source adapter).
