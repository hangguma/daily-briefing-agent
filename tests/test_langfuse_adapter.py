"""
Unit tests for the Langfuse observability adapter.

Verifies the toggle guards, the explicit auth check (the AgentOps lesson:
bad credentials must fail LOUDLY at startup, not silently at export), and
graceful degradation. langfuse/openinference are patched so no real
network/dashboard call happens.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from config import settings
from observability import langfuse_adapter
from observability.langfuse_adapter import end_session, start_session


def _reset():
    langfuse_adapter._client = None


def _fake_modules(client):
    """Build the fake module tree the adapter imports from."""
    instrumentor = MagicMock()
    return {
        "langfuse": SimpleNamespace(get_client=lambda: client),
        "openinference.instrumentation.crewai": SimpleNamespace(
            CrewAIInstrumentor=lambda: instrumentor
        ),
        "openinference.instrumentation.litellm": SimpleNamespace(
            LiteLLMInstrumentor=lambda: instrumentor
        ),
    }


def test_start_skips_when_disabled():
    _reset()
    with patch.object(settings, "LANGFUSE_ENABLED", False):
        assert start_session() is False


def test_start_skips_when_no_keys():
    _reset()
    with patch.object(settings, "LANGFUSE_ENABLED", True), \
         patch.object(settings, "LANGFUSE_PUBLIC_KEY", ""), \
         patch.object(settings, "LANGFUSE_SECRET_KEY", ""):
        assert start_session() is False


def test_start_fails_loudly_on_bad_auth():
    # auth_check False -> start_session returns False and no client is kept.
    # This is the core lesson from the AgentOps incident (silent export failure).
    _reset()
    client = SimpleNamespace(auth_check=lambda: False)
    with patch.object(settings, "LANGFUSE_ENABLED", True), \
         patch.object(settings, "LANGFUSE_PUBLIC_KEY", "pk"), \
         patch.object(settings, "LANGFUSE_SECRET_KEY", "sk"), \
         patch.dict(sys.modules, _fake_modules(client)):
        assert start_session() is False
    assert langfuse_adapter._client is None


def test_start_success_instruments_and_keeps_client():
    _reset()
    client = SimpleNamespace(auth_check=lambda: True)
    with patch.object(settings, "LANGFUSE_ENABLED", True), \
         patch.object(settings, "LANGFUSE_PUBLIC_KEY", "pk"), \
         patch.object(settings, "LANGFUSE_SECRET_KEY", "sk"), \
         patch.dict(sys.modules, _fake_modules(client)):
        assert start_session() is True
    assert langfuse_adapter._client is client
    _reset()


def test_start_graceful_on_error():
    # If get_client raises, start_session must return False (not crash)
    _reset()

    def boom():
        raise RuntimeError("sdk exploded")

    mods = _fake_modules(None)
    mods["langfuse"] = SimpleNamespace(get_client=boom)
    with patch.object(settings, "LANGFUSE_ENABLED", True), \
         patch.object(settings, "LANGFUSE_PUBLIC_KEY", "pk"), \
         patch.object(settings, "LANGFUSE_SECRET_KEY", "sk"), \
         patch.dict(sys.modules, mods):
        assert start_session() is False


def test_end_session_noop_without_client():
    _reset()
    end_session(success=True)  # must not raise


def test_end_session_flushes_and_clears():
    _reset()
    client = MagicMock()
    langfuse_adapter._client = client
    end_session(success=True)
    client.flush.assert_called_once()
    assert langfuse_adapter._client is None


def test_end_session_graceful_on_flush_error():
    _reset()
    client = MagicMock()
    client.flush.side_effect = RuntimeError("flush failed")
    langfuse_adapter._client = client
    end_session(success=False)  # must not raise
    assert langfuse_adapter._client is None
