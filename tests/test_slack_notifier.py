"""
Unit tests for the Slack output adapter.

Mocks requests.post so no real Slack call is made. Verifies:
- Block Kit structure (header / section / context)
- enabled/disabled and missing-URL guards
- graceful degradation (network error / non-200 -> returns False, no crash)
- long body truncation
"""

from unittest.mock import MagicMock, patch

from config import settings
from models.schemas import BriefingReport
from notifiers.slack_notifier import build_blocks, send_to_slack


def _report(markdown="# News Briefing\n- item"):
    return BriefingReport(date="2026-06-09", keywords=["AI", "agents"], markdown=markdown)


def test_build_blocks_structure():
    blocks = build_blocks(_report())
    types = [b["type"] for b in blocks]
    assert types[0] == "header"           # title first
    assert "section" in types             # body present
    assert types[-1] == "context"         # keyword footer last
    # keywords appear in the context footer
    assert "AI" in blocks[-1]["elements"][0]["text"]


def test_build_blocks_truncates_long_body():
    long_md = "x" * 5000
    blocks = build_blocks(_report(markdown=long_md))
    section = next(b for b in blocks if b["type"] == "section")
    assert len(section["text"]["text"]) < 3000   # under Slack's limit
    assert "truncated" in section["text"]["text"]


def test_send_skips_when_disabled():
    with patch.object(settings, "SLACK_ENABLED", False):
        assert send_to_slack(_report()) is False


def test_send_skips_when_no_url():
    with patch.object(settings, "SLACK_ENABLED", True), \
         patch.object(settings, "SLACK_WEBHOOK_URL", ""):
        assert send_to_slack(_report()) is False


@patch("notifiers.slack_notifier.requests.post")
def test_send_success(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    with patch.object(settings, "SLACK_ENABLED", True), \
         patch.object(settings, "SLACK_WEBHOOK_URL", "https://hooks.slack.com/x"):
        assert send_to_slack(_report()) is True
    # payload carries blocks
    _, kwargs = mock_post.call_args
    assert "blocks" in kwargs["json"]


@patch("notifiers.slack_notifier.requests.post")
def test_send_non_200_returns_false(mock_post):
    mock_post.return_value = MagicMock(status_code=400, text="bad_request")
    with patch.object(settings, "SLACK_ENABLED", True), \
         patch.object(settings, "SLACK_WEBHOOK_URL", "https://hooks.slack.com/x"):
        assert send_to_slack(_report()) is False   # no crash


@patch("notifiers.slack_notifier.requests.post")
def test_send_network_error_graceful(mock_post):
    mock_post.side_effect = Exception("connection refused")
    with patch.object(settings, "SLACK_ENABLED", True), \
         patch.object(settings, "SLACK_WEBHOOK_URL", "https://hooks.slack.com/x"):
        assert send_to_slack(_report()) is False   # exception absorbed
