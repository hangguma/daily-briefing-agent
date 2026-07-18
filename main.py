"""
Phase 1 entry point - runs the briefing agent from the command line.

Usage:
    python main.py
    python main.py --keywords "agentic AI" "RAG" "vector DB"

In Phase 2, app.py (Streamlit) calls build_crew instead of this file.
The agent logic (crew.py) is reused as-is.
"""

import argparse
import os
from datetime import date, datetime

from config import settings
from config.logging_setup import setup_logging
from crew import build_crew
from notifiers.slack_notifier import send_to_slack
from observability.langfuse_adapter import end_session, start_session


def parse_args() -> list[str]:
    """Read keywords from CLI args; fall back to defaults if absent."""
    parser = argparse.ArgumentParser(description="Daily Briefing Agent")
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=settings.DEFAULT_KEYWORDS,
        help="Keywords for the briefing (space-separated, up to 5 recommended)",
    )
    args = parser.parse_args()
    return args.keywords[:5]  # safely cap at 5


def format_search_conditions(keywords: list[str]) -> str:
    """Build a Markdown footer describing the search conditions used.

    Why code, not the LLM?
    - Search conditions are deterministic, known-exactly values from settings.
      Leaving them to the LLM risks guesses/hallucination, so code injects them
      to always match reality. (Same principle as Review #2.)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    keyword_str = ", ".join(f"`{k}`" for k in keywords)
    return (
        "\n\n---\n"
        "## Search conditions for this briefing\n\n"
        f"| Item | Value |\n"
        f"| --- | --- |\n"
        f"| Keywords | {keyword_str} |\n"
        f"| Articles per keyword | {settings.RESULTS_PER_KEYWORD} |\n"
        f"| Final selection | top {settings.TOP_N_ARTICLES} |\n"
        f"| Time window | last {settings.SEARCH_DAYS} days |\n"
        f"| Search category | {settings.SEARCH_TOPIC} |\n"
        f"| Search depth | {settings.SEARCH_DEPTH} |\n"
        f"| Model | {settings.LLM_MODEL} |\n"
        f"| Generated at | {now} |\n"
    )


def save_report(markdown: str) -> str:
    """Save the Markdown briefing to the outputs/ folder as a .md file.

    If a briefing for today already exists (re-run), append a time suffix
    instead of silently overwriting the earlier one.
    """
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    today = date.today().isoformat()
    path = os.path.join(settings.OUTPUT_DIR, f"briefing_{today}.md")
    if os.path.exists(path):
        stamp = datetime.now().strftime("%H%M")
        path = os.path.join(settings.OUTPUT_DIR, f"briefing_{today}_{stamp}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


def main() -> None:
    # 0) Set up logging (console + file under outputs/logs/)
    log = setup_logging(to_file=True)

    # 1) Check API keys before running (fail early)
    settings.validate()

    keywords = parse_args()
    log.info("Starting briefing - keywords: %s", ", ".join(keywords))

    # 1-1) Start observability tracing (optional, toggled). Must run before kickoff.
    start_session()

    # 2) Assemble and run the Crew
    crew = build_crew(keywords)
    try:
        result = crew.kickoff()
    except Exception as e:  # noqa: BLE001
        # [Review #3] Handle runtime errors: auth failure, network, token limits.
        # validate() only checks key presence; key *validity* surfaces here.
        log.error("Failed to generate the briefing: %s", e)
        log.error("  - Check ANTHROPIC_API_KEY / TAVILY_API_KEY validity.")
        log.error("  - Check your network connection and API usage limits.")
        end_session(success=False)
        return

    # 3) Extract result - structured object thanks to output_pydantic
    #    (string fallback in case of older versions / parse failure)
    report = getattr(result, "pydantic", None)
    markdown = report.markdown if report else str(result)

    # 3-1) Append search-condition metadata in code (deterministic, factual)
    markdown += format_search_conditions(keywords)

    # 4) Save + print
    path = save_report(markdown)
    print("\n" + "=" * 50)
    print(markdown)
    print("=" * 50)
    log.info("Briefing complete -> %s", path)

    # 5) Push to Slack (output adapter). Safe no-op if disabled/unset.
    #    The file is already saved, so a Slack failure never aborts the run.
    if report is not None:
        send_to_slack(report)

    # 6) Close observability session (safe no-op if not active)
    end_session(success=True)


if __name__ == "__main__":
    main()
