"""
AgentOps observability adapter - Phase 2.

Why this design?
- AgentOps traces the whole crew run (agent steps, tool calls, LLM cost) to a
  web dashboard. Once initialized, CrewAI runs are captured automatically.
- This is an OBSERVABILITY adapter, mirroring our input/output adapters: the
  crew and agents are untouched. We only wrap initialization here.
- Toggled by settings (AGENTOPS_ENABLED) and fully optional. If disabled,
  unset, or the SDK fails, the run proceeds normally (graceful degradation):
  observability must never break the actual briefing.

Setup:
- Get an API key at https://app.agentops.ai
- Put AGENTOPS_API_KEY in .env and set AGENTOPS_ENABLED=true
- After a run, AgentOps prints a clickable dashboard URL to the console.
"""

import logging

from config import settings

log = logging.getLogger("briefing")


def start_session() -> bool:
    """Initialize AgentOps tracing if enabled. Returns True if started.

    Call once at the start of a run (entry point), before build_crew().
    Never raises - failures are logged and tracing is simply skipped.
    """
    if not settings.AGENTOPS_ENABLED:
        log.info("[agentops] disabled (AGENTOPS_ENABLED is not true), skipping.")
        return False
    if not settings.AGENTOPS_API_KEY:
        log.info("[agentops] AGENTOPS_API_KEY is not set, skipping.")
        return False

    try:
        import agentops

        # auto_start_session=True lets AgentOps manage the trace lifecycle and
        # auto-capture the CrewAI run. We close it explicitly in end_session().
        agentops.init(settings.AGENTOPS_API_KEY, auto_start_session=True)
        log.info("[agentops] tracing started - see app.agentops.ai for the dashboard.")
        return True
    except Exception as e:  # noqa: BLE001 (observability must not break the run)
        log.error("[agentops] failed to start tracing: %s", e)
        return False


def end_session(success: bool = True) -> None:
    """Close the AgentOps trace at the end of a run. Safe no-op if not active.

    Uses end_trace() (end_session() is deprecated and removed in AgentOps v4).
    """
    if not settings.AGENTOPS_ENABLED:
        return
    try:
        import agentops

        state = agentops.TraceState.SUCCESS if success else agentops.TraceState.ERROR
        agentops.end_trace(end_state=state)
    except Exception as e:  # noqa: BLE001
        log.error("[agentops] failed to end trace: %s", e)
