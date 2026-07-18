# 📰 Daily Briefing Agent

[![CI](https://github.com/hangguma/daily-briefing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/hangguma/daily-briefing-agent/actions/workflows/ci.yml)

A multi-agent system that automatically **collects → curates → summarizes** daily news based on your keywords.
Built as a 3-agent sequential pipeline with [CrewAI](https://crewai.com).

## 🎯 What It Does

```
Enter keywords  →  Auto-collect news  →  Dedupe & rank by importance  →  Generate Markdown briefing
```

Three specialized agents collaborate:

| Agent | Role | Tool |
|---|---|---|
| **Collector** | Searches & collects latest news by keyword | Tavily Search + RSS feeds |
| **Ranker** | Removes duplicates + scores importance | (LLM reasoning) |
| **Writer** | 3-line summaries + Markdown briefing | (LLM writing) |

## 🏗️ Architecture

```
User keywords
    ↓
[Collector] ──(Tavily + RSS)──> Raw article list
    ↓
[Ranker] ────────────────────> Top-N ranked articles
    ↓
[Writer] ──(Claude)──────────> Markdown briefing (.md) ──> Slack (optional)
```

Design principles: **single responsibility** · **explicit I/O contracts (Pydantic)** · **observability (verbose)** · **graceful degradation (retry on search failure)**

## 🚀 Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY and TAVILY_API_KEY

# 3. Run
python main.py

# Or specify keywords directly
python main.py --keywords "agentic AI" "RAG" "vector database"
```

Output is saved to `outputs/briefing_YYYY-MM-DD.md`.

## 🧪 Testing

```bash
pytest -v
```

Unit tests run without real API keys — external APIs are mocked. CI runs the full suite on every push via GitHub Actions.

## 📁 Project Structure

```
daily-briefing-agent/
├── agents/        # Agent definitions (role, goal, backstory)
├── tasks/         # Task definitions (what to do)
├── tools/         # External tool wrappers (Tavily search)
├── models/        # Data models (Pydantic schemas)
├── config/        # Settings & environment variables
├── tests/         # Unit tests
├── crew.py        # Agent system assembly (reusable core)
└── main.py        # CLI entry point
```

## 🛣️ Roadmap

- [x] **Phase 1** — Local CLI version
- [x] **Phase 2** — Streamlit web UI (reuses `crew.py`; `app.py` entry point) + RSS multi-source + Slack delivery + AgentOps observability
- [ ] **Phase 3** — Scheduler (cron) auto-delivery

## 🧰 Tech Decision Notes

> **Why CrewAI?** Intuitive for role-based multi-agent collaboration and ideal
> for rapid prototyping. The simple sequential workflow keeps debugging easy.
> Once production-grade state management and conditional branching are needed,
> migration to **LangGraph** is planned (a common industry learning path).

## 📦 Tech Stack

`Python` · `CrewAI` · `Claude API` · `Tavily` · `Pydantic`

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
