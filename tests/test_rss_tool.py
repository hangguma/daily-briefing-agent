"""
Unit tests for the RSS source adapter.

Mocks feedparser.parse so no real network is needed; verifies only our logic:
- keyword-match filter
- freshness (date) filter
- graceful degradation (empty result on parse failure)
"""

import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from tools.rss_tool import RssFetchTool


def _entry(title, link, summary, days_ago):
    """Build a fake feedparser entry (published_parsed is UTC, like feedparser)."""
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {
        "title": title,
        "link": link,
        "summary": summary,
        "published_parsed": time.struct_time(dt.timetuple()),
    }


def _feed(entries):
    """Build a fake feedparser result (object with .entries)."""
    return SimpleNamespace(entries=entries, feed=SimpleNamespace(title="Test"))


@patch("tools.rss_tool.feedparser.parse")
def test_only_keyword_matched_items(mock_parse):
    mock_parse.return_value = _feed([
        _entry("OpenAI launches agentic AI model", "https://x.com/1", "...", 1),
        _entry("New pasta recipe", "https://x.com/2", "cooking tips", 1),
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://feed"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True):
        out = RssFetchTool()._run(keywords=["agentic AI"])
    assert "OpenAI launches" in out      # matched
    assert "pasta" not in out             # not matched -> excluded


@patch("tools.rss_tool.feedparser.parse")
def test_freshness_filter_drops_old(mock_parse):
    mock_parse.return_value = _feed([
        _entry("Recent AI news", "https://x.com/1", "...", 1),       # recent
        _entry("Old AI news", "https://x.com/2", "...", 999),        # old
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://feed"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True), \
         patch.object(settings, "SEARCH_DAYS", 7):
        out = RssFetchTool()._run(keywords=["AI"])
    assert "Recent AI news" in out
    assert "Old AI news" not in out       # older than 7 days -> excluded


@patch("tools.rss_tool.feedparser.parse")
def test_iterates_all_feeds(mock_parse):
    mock_parse.return_value = _feed([
        _entry("AI breakthrough", "https://x.com/1", "...", 1),
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://a", "http://b", "http://c"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True):
        RssFetchTool()._run(keywords=["AI"])
    assert mock_parse.call_count == 3     # all 3 feeds called


@patch("tools.rss_tool.feedparser.parse")
def test_parse_failure_graceful_degradation(mock_parse):
    # One feed raising must not crash the whole run; returns empty-result message
    mock_parse.side_effect = Exception("feed down")
    with patch.object(settings, "RSS_FEEDS", ["http://broken"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True):
        out = RssFetchTool()._run(keywords=["AI"])
    assert "No recent articles matched" in out  # handled safely, no crash


@patch("tools.rss_tool.feedparser.parse")
def test_filter_off_collects_all(mock_parse):
    mock_parse.return_value = _feed([
        _entry("AI news", "https://x.com/1", "...", 1),
        _entry("Cooking news", "https://x.com/2", "...", 1),
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://feed"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", False):
        out = RssFetchTool()._run(keywords=["AI"])
    assert "AI news" in out
    assert "Cooking news" in out          # filter off -> both included


@patch("tools.rss_tool.feedparser.parse")
def test_korean_keyword_matching(mock_parse):
    # Keywords may be Korean or English; matching must work for both
    mock_parse.return_value = _feed([
        _entry("오늘의 인공지능 소식", "https://x.com/1", "최신 동향", 1),
        _entry("Today's cooking tips", "https://x.com/2", "recipes", 1),
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://feed"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True):
        out = RssFetchTool()._run(keywords=["인공지능"])
    assert "인공지능 소식" in out      # Korean keyword matched
    assert "cooking" not in out         # unrelated English item excluded


@patch("tools.rss_tool.feedparser.parse")
def test_english_match_is_case_insensitive(mock_parse):
    # English matching ignores case; Korean has no case so it's unaffected
    mock_parse.return_value = _feed([
        _entry("OpenAI launches new MODEL", "https://x.com/1", "...", 1),
    ])
    with patch.object(settings, "RSS_FEEDS", ["http://feed"]), \
         patch.object(settings, "RSS_KEYWORD_FILTER", True):
        out = RssFetchTool()._run(keywords=["model"])  # lowercase query
    assert "OpenAI launches" in out      # matched despite case difference
