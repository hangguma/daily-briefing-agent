"""
Unit tests for the AgentOps observability adapter.

Verifies the toggle guards and graceful degradation. agentops itself is patched
where needed so no real network/dashboard call happens.
"""

import sys
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from observability.agentops_adapter import end_session, start_session


def test_start_skips_when_disabled():
    with patch.object(settings, "AGENTOPS_ENABLED", False):
        assert start_session() is False


def test_start_skips_when_no_key():
    with patch.object(settings, "AGENTOPS_ENABLED", True), \
         patch.object(settings, "AGENTOPS_API_KEY", ""):
        assert start_session() is False


def test_start_success_calls_init():
    fake = SimpleNamespace(init=lambda *a, **k: None)
    with patch.object(settings, "AGENTOPS_ENABLED", True), \
         patch.object(settings, "AGENTOPS_API_KEY", "ao-key"), \
         patch.dict(sys.modules, {"agentops": fake}):
        assert start_session() is True


def test_start_graceful_on_error():
    # If agentops.init raises, start_session must return False (not crash)
    def boom(*a, **k):
        raise RuntimeError("init failed")

    fake = SimpleNamespace(init=boom)
    with patch.object(settings, "AGENTOPS_ENABLED", True), \
         patch.object(settings, "AGENTOPS_API_KEY", "ao-key"), \
         patch.dict(sys.modules, {"agentops": fake}):
        assert start_session() is False


def test_end_session_noop_when_disabled():
    # Should simply return without touching agentops
    with patch.object(settings, "AGENTOPS_ENABLED", False):
        end_session(success=True)  # must not raise


def test_end_session_graceful_on_error():
    def boom(*args, **kwargs):
        raise RuntimeError("end failed")

    fake = SimpleNamespace(
        end_trace=boom,
        TraceState=SimpleNamespace(SUCCESS="SUCCESS", ERROR="ERROR"),
    )
    with patch.object(settings, "AGENTOPS_ENABLED", True), \
         patch.dict(sys.modules, {"agentops": fake}):
        end_session(success=True)  # error absorbed, must not raise


def test_end_session_calls_end_trace():
    calls = {}

    def fake_end_trace(end_state=None):
        calls["end_state"] = end_state

    fake = SimpleNamespace(
        end_trace=fake_end_trace,
        TraceState=SimpleNamespace(SUCCESS="SUCCESS", ERROR="ERROR"),
    )
    with patch.object(settings, "AGENTOPS_ENABLED", True), \
         patch.dict(sys.modules, {"agentops": fake}):
        end_session(success=False)
    assert calls["end_state"] == "ERROR"   # uses end_trace, not end_session
