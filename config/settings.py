"""
Global project settings.

Why this design?
- Hardcoding API keys leaks them when pushed to git. Keys are kept in a .env
  file and read via os.getenv.
- "Values that change" (keywords, model name) are centralized here so the
  Streamlit UI (Phase 2) can inject them dynamically without touching logic.
"""

import os

from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()

# -- API keys -------------------------------------------------
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# -- Slack (Phase 2: output adapter) --------------------------
# Incoming Webhook URL. Keep it secret - never commit it (use .env / Lambda env).
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
# When True, the briefing is pushed to Slack after generation.
SLACK_ENABLED: bool = os.getenv("SLACK_ENABLED", "false").lower() == "true"

# -- Langfuse (Phase 2: observability adapter) ----------------
# Dashboard + span tracing for the crew (OpenTelemetry-based).
# Replaced AgentOps 2026-07-17: its span export failed silently (empty
# dashboard, no error). Keys at https://cloud.langfuse.com (free tier).
LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
# When True (and keys set + auth verified), runs are traced to the dashboard.
LANGFUSE_ENABLED: bool = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

# -- LLM config -----------------------------------------------
# CrewAI uses LiteLLM under the hood, hence the "anthropic/<model>" format.
LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")
# Output token budget must include reasoning ("thinking") tokens. With the
# 4096 default, a long thinking phase can consume the whole budget and the
# response gets truncated before any text block, which CrewAI surfaces as an
# intermittent "Invalid response from LLM call" failure.
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "16384"))

# -- Pipeline parameters --------------------------------------
# In Phase 2 these are surfaced as UI inputs.
# Keywords may be English, Korean, or mixed (e.g. "AI", "인공지능").
DEFAULT_KEYWORDS: list[str] = ["agentic AI", "LLM agents", "AI startup funding"]
RESULTS_PER_KEYWORD: int = 5   # articles per keyword from search
TOP_N_ARTICLES: int = 6        # top articles kept in the final briefing
SEARCH_DAYS: int = 7           # only news within the last N days (freshness)
SEARCH_TOPIC: str = "news"     # Tavily search category (news / general)
SEARCH_DEPTH: str = "basic"    # search depth (basic=cheap / advanced=richer)

# -- RSS sources (Phase 2: multi-source) ----------------------
# List of media RSS feed URLs to subscribe to. Add/remove freely.
# Why in settings? It changes often, so it belongs in config, not code.
RSS_FEEDS: list[str] = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
]
RSS_KEYWORD_FILTER: bool = True  # True: only keyword-matched items; False: all recent items

# -- Output config --------------------------------------------
OUTPUT_DIR: str = "outputs"


def validate() -> None:
    """Check required API keys are set before running."""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}\n"
            f"Copy .env.example to .env and fill in your keys."
        )
