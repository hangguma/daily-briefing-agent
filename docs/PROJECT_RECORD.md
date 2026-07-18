# 📒 Project Record — Daily Briefing Agent

> A multi-agent project built to learn Agentic AI and serve as a portfolio piece.
> A retrospective documenting the full 8-stage workflow, from planning to deployment.

---

## 1. One-Line Summary

A CrewAI-based 3-agent system that takes keywords and turns the latest news into a briefing: **auto-collect → dedupe & curate → summarize**.

---

## 2. Why This Project

- **Learning goal:** Hands-on experience building autonomous (Agentic AI) systems
- **Why this topic:** It exercises the core multi-agent patterns (role division, tool use, sequential collaboration) in the shortest possible timeframe
- **Market context:** Many companies claim to have "adopted" agents, but few run them in production — so the ability to ship something that *actually works* is valuable

---

## 3. The 8-Stage Development Workflow

| Stage | Key Decision / Deliverable |
|---|---|
| 1. Market Research | Compared agent market & frameworks (LangGraph / CrewAI / AutoGen) |
| 2. Idea Brainstorm | Picked Daily Briefing (shortest timeline) among 3 candidates |
| 3. Requirements | Functional/non-functional reqs, acceptance criteria, 2-phase hosting plan |
| 4. Architecture | Sequential Pipeline + Pydantic I/O contracts + modular structure |
| 5. Code | Implemented with agents/tasks/tools/models/config structure |
| 6. Review | Found & fixed 6 issues via static analysis + manual review |
| 7. Test | 18 unit tests + manual UAT doc + real end-to-end run |
| 8. Deployment | GitHub upload + GitHub Actions CI + deployment roadmap |

---

## 4. Architecture

```
User keywords
    ↓
[Collector] ──(Tavily)──> Raw article list
    ↓
[Ranker] ──────────────> Top-N ranked articles
    ↓
[Writer] ──(Claude)────> Markdown briefing (.md)
```

- **3 agents**, each with a single responsibility (collect / rank / write)
- **CrewAI `Process.sequential`** for ordered execution
- **crew.py (logic) ↔ main.py (execution) separation** → Phase 2 only swaps the execution layer

---

## 5. Key Technical Decisions & Rationale

### 5-1. Chose CrewAI (over LangGraph)
- Intuitive for role-based collaboration, fast prototyping, easy-to-debug sequential flow
- Its downsides (opaque abstractions in complex flows, token overhead) don't apply to this simple structure
- Designed a learning path to **move to LangGraph in the next project** (framework comparison = portfolio strength)

### 5-2. Pydantic I/O Contracts
- Fixed inter-agent data formats as models → blocks malformed data from passing downstream
- Applied `output_pydantic` on each Task to turn the contract from "documentation" into "enforcement"

### 5-3. Deterministic Values Are Injected by Code
- Values that can be known exactly (date, search conditions) are injected by code, not left to the LLM
- A design principle that eliminates LLM hallucination at the source (derived in Review → reapplied when adding features)

---

## 6. Debugging Log (Solved Hands-On)

The most valuable part of this project. Real-environment problems not found in tutorials, solved one by one.

| Symptom | Root Cause | Fix |
|---|---|---|
| `No matching distribution found for crewai` | Python 3.9 (crewai requires 3.10+) | Recreated venv with Python 3.12 |
| `ResolutionImpossible` | `python-dotenv` pin conflict (1.0.1 vs crewai's >=1.2.2) | Matched requirements to crewai's range |
| `404 not_found_error: model` | Model ID (`claude-sonnet-4-20250514`) was retired | Swapped to current `claude-sonnet-4-6` |

**Lessons learned**
- "It imports != it runs" — some issues surface only at real execution
- Dependency conflicts are pinpointed by the `conflict is caused by` line in the error
- Don't guess model IDs or library versions — verify against official docs

---

## 7. Testing Strategy

| Aspect | Automated (pytest) | Manual (UAT doc) |
|---|---|---|
| Verifies | Internal logic (contracts, retries, parsing) | Real API execution path, output quality |
| API | Mocked (fake) | Real keys |
| Result | 18 passed | 9-case checklist |

- External API (Tavily) isolated with `unittest.mock` -> fast, free, stable
- CI (GitHub Actions) auto-runs all 18 tests on every push

---

## 8. Automation Perspective (System End Goal)

| Component | Manual | Semi-auto | Fully-auto |
|---|---|---|---|
| Execution | Terminal manual run | Streamlit button | cron scheduler |
| Keywords | Manual input | Saved profile | Interest-recommendation agent |
| Delivery | Check file | Copy | Auto-send to Slack/email |

-> Phase 3 (daily auto-briefing) is the first realization of a "self-running agent."

---

## 9. Next Steps

- [ ] **Phase 2** — Streamlit web UI (reuse crew.py, live demo link)
- [ ] **Phase 3** — GitHub Actions `schedule` + Slack auto-delivery
- [ ] **Next project** — PR Reviewer (LangGraph-based; learn parallel & conditional branching)

---

## 10. Retrospective in One Line

> This wasn't just writing code — it was driving the entire process of
> **plan -> design -> build -> review -> test -> deploy** through my own judgment,
> gaining real-world debugging and CI automation experience along the way.

---

**Tech stack:** Python · CrewAI · Claude API · Tavily · Pydantic · pytest · GitHub Actions
