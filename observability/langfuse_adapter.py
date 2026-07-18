"""
Langfuse observability adapter - replaces the AgentOps adapter.

Why the switch (2026-07-17)?
- AgentOps 0.4.x generated trace URLs locally but span export silently failed
  ("Authentication failed - will continue without authentication"): the
  dashboard stayed empty with no error surfaced. Server-side check confirmed
  the traces never existed. An observability tool that fails silently defeats
  its own purpose.
- Lesson encoded here: verify auth EXPLICITLY at startup (auth_check) and log
  loudly when it fails, instead of discovering an empty dashboard days later.

Why this design?
- Same adapter interface as before (start_session / end_session), so entry
  points swap one import and the crew/agents remain untouched.
- Langfuse v3+ is OpenTelemetry-based; CrewAI + LiteLLM spans come from
  OpenInference instrumentors and are exported to Langfuse.
- Toggled by settings (LANGFUSE_ENABLED) and fully optional: if disabled,
  unset, or the SDK fails, the run proceeds normally (graceful degradation).

Setup:
- Sign up at https://cloud.langfuse.com (free tier), create a project
- Put LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST in .env
  and set LANGFUSE_ENABLED=true
- Traces appear at cloud.langfuse.com under the project after each run
"""

import logging

from config import settings

log = logging.getLogger("briefing")

_client = None


def start_session() -> bool:
    """Initialize Langfuse tracing if enabled. Returns True if started.

    Call once at the start of a run (entry point), before build_crew().
    Never raises - failures are logged and tracing is simply skipped.
    Auth is checked explicitly so a bad key fails LOUDLY here, not silently
    at export time.
    """
    global _client

    if not settings.LANGFUSE_ENABLED:
        log.info("[langfuse] disabled (LANGFUSE_ENABLED is not true), skipping.")
        return False
    if not (settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY):
        log.info("[langfuse] keys are not set, skipping.")
        return False

    try:
        from langfuse import get_client
        from openinference.instrumentation.crewai import CrewAIInstrumentor
        from openinference.instrumentation.litellm import LiteLLMInstrumentor

        _client = get_client()  # reads LANGFUSE_* env vars

        # Fail loudly on bad credentials (the AgentOps lesson).
        if not _client.auth_check():
            log.error(
                "[langfuse] AUTH FAILED - check LANGFUSE_PUBLIC_KEY / "
                "LANGFUSE_SECRET_KEY / LANGFUSE_HOST. Tracing is OFF for this run."
            )
            _client = None
            return False

        CrewAIInstrumentor().instrument(skip_dep_check=True)
        LiteLLMInstrumentor().instrument()
        log.info(
            "[langfuse] tracing started (auth verified) - see %s for the dashboard.",
            settings.LANGFUSE_HOST,
        )
        return True
    except Exception as e:  # noqa: BLE001 (observability must not break the run)
        log.error("[langfuse] failed to start tracing: %s", e)
        _client = None
        return False


def end_session(success: bool = True) -> None:
    """Flush buffered spans at the end of a run. Safe no-op if not active.

    Explicit flush guarantees delivery before the process exits - async
    exporters dropping data at shutdown was part of the AgentOps failure mode.
    """
    global _client
    if _client is None:
        return
    try:
        _client.flush()
        log.info("[langfuse] trace flushed (run %s).", "succeeded" if success else "failed")
    except Exception as e:  # noqa: BLE001
        log.error("[langfuse] failed to flush trace: %s", e)
    finally:
        _client = None
