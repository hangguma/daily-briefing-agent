"""
Slack output adapter - Phase 2.

Why this design?
- Builds Slack Block Kit JSON directly from the structured BriefingReport,
  not by re-parsing the markdown. Structured input is far more reliable.
- Same graceful-degradation philosophy as the source adapters: if Slack fails,
  the briefing file is already saved, so we log and move on (never crash).
- This is an OUTPUT adapter, mirroring the input adapters (Tavily/RSS). The
  crew and agents are untouched; this only consumes BriefingReport.

Slack mrkdwn differs from standard markdown:
  *bold* (one asterisk), <url|text> for links. Block Kit handles structure.
"""

import requests

import logging

from config import settings
from models.schemas import BriefingReport

log = logging.getLogger("briefing")

# Slack limits: keep each text block under ~3000 chars, <=50 blocks per message.
_MAX_TEXT = 2900
_MAX_BLOCKS = 48


def build_blocks(report: BriefingReport) -> list[dict]:
    """Convert a BriefingReport into Slack Block Kit blocks.

    The Writer already produced the markdown body; here we wrap it into a
    header + section + context footer. We keep it simple and robust rather
    than trying to re-split every article into its own block.
    """
    keyword_str = ", ".join(report.keywords)

    # Body text: Slack section blocks cap around 3000 chars, so truncate safely.
    body = report.markdown
    if len(body) > _MAX_TEXT:
        body = body[:_MAX_TEXT] + "\n... (truncated; see full briefing file)"

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"News Briefing ({report.date})"},
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": body}},
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Keywords: {keyword_str}"}
            ],
        },
    ]
    return blocks[:_MAX_BLOCKS]


def send_to_slack(report: BriefingReport) -> bool:
    """Push the briefing to Slack. Returns True on success, False otherwise.

    Never raises: failures are logged so the overall run is not aborted
    (the briefing file has already been saved by the caller).
    """
    if not settings.SLACK_ENABLED:
        log.info("[slack] disabled (SLACK_ENABLED is not true), skipping.")
        return False
    if not settings.SLACK_WEBHOOK_URL:
        log.info("[slack] SLACK_WEBHOOK_URL is not set, skipping.")
        return False

    payload = {"blocks": build_blocks(report)}
    try:
        resp = requests.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            log.info("[slack] briefing delivered.")
            return True
        log.error("[slack] delivery failed: %s %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:  # noqa: BLE001 (graceful degradation)
        log.error("[slack] delivery error: %s", e)
        return False
