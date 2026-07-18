"""
Streamlit web UI - Phase 2 on-demand entry point.

Why this design?
- This is another ENTRY POINT (a "driver"), like main.py. It reuses crew.py
  (the engine) and slack_notifier (the output adapter) without modifying them.
- main.py drives from the terminal; app.py drives from the browser. The agent
  logic is identical and shared.

Run locally:
    streamlit run app.py
"""

from datetime import date, datetime

import streamlit as st

from config import settings
from config.logging_setup import setup_logging
from crew import build_crew
from notifiers.slack_notifier import send_to_slack
from observability.langfuse_adapter import end_session, start_session


def _footer(keywords: list[str]) -> str:
    """Build the same search-conditions footer used by the CLI."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    keyword_str = ", ".join(f"`{k}`" for k in keywords)
    return (
        "\n\n---\n"
        "## Search conditions for this briefing\n\n"
        f"| Item | Value |\n| --- | --- |\n"
        f"| Keywords | {keyword_str} |\n"
        f"| Articles per keyword | {settings.RESULTS_PER_KEYWORD} |\n"
        f"| Final selection | top {settings.TOP_N_ARTICLES} |\n"
        f"| Time window | last {settings.SEARCH_DAYS} days |\n"
        f"| Model | {settings.LLM_MODEL} |\n"
        f"| Generated at | {now} |\n"
    )


def run_briefing(keywords: list[str]):
    """Assemble and run the crew. Returns the BriefingReport or None."""
    start_session()  # observability tracing (optional, toggled)
    try:
        crew = build_crew(keywords)
        result = crew.kickoff()
        end_session(success=True)
        return getattr(result, "pydantic", None), result
    except Exception:
        end_session(success=False)
        raise


setup_logging(to_file=True)

# -- Page setup -──────────────────────────────────────────────
st.set_page_config(page_title="Daily Briefing Agent", page_icon="📰")
st.title("📰 Daily Briefing Agent")
st.caption("Multi-source news briefing - search (Tavily) + subscription (RSS)")

# Session state holds the last result so the Slack button can reuse it
if "report" not in st.session_state:
    st.session_state.report = None
    st.session_state.markdown = ""

# ── Input form ───────────────────────────────────────────────
with st.form("briefing_form"):
    raw = st.text_input(
        "Keywords (comma-separated, Korean or English)",
        value=", ".join(settings.DEFAULT_KEYWORDS),
        help="e.g. AI, 인공지능, machine learning",
    )
    submitted = st.form_submit_button("Generate briefing")

if submitted:
    keywords = [k.strip() for k in raw.split(",") if k.strip()][:5]
    if not keywords:
        st.warning("Please enter at least one keyword.")
    else:
        try:
            settings.validate()
        except ValueError as e:
            st.error(str(e))
        else:
            with st.spinner(f"Generating briefing for: {', '.join(keywords)} ..."):
                try:
                    report, raw_result = run_briefing(keywords)
                    markdown = (report.markdown if report else str(raw_result))
                    markdown += _footer(keywords)
                    st.session_state.report = report
                    st.session_state.markdown = markdown
                    st.session_state.keywords = keywords
                except Exception as e:  # noqa: BLE001
                    st.error(f"Failed to generate the briefing: {e}")

# ── Result display ───────────────────────────────────────────
if st.session_state.markdown:
    st.markdown(st.session_state.markdown)

    # Download button
    today = date.today().isoformat()
    st.download_button(
        "Download .md",
        data=st.session_state.markdown,
        file_name=f"briefing_{today}.md",
        mime="text/markdown",
    )

    # Slack send button (reuses the Step 2 adapter)
    if st.button("Send to Slack"):
        if st.session_state.report is None:
            st.warning("No structured report available to send.")
        elif send_to_slack(st.session_state.report):
            st.success("Sent to Slack.")
        else:
            st.error(
                "Slack send failed or is disabled. "
                "Check SLACK_ENABLED=true and SLACK_WEBHOOK_URL in your .env."
            )
