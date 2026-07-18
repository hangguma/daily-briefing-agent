"""
Unit tests for the search tool.

Mocks TavilyClient instead of calling the real API.
Why?
- Tests that depend on an external API are slow and flaky (network/billing).
- We verify OUR retry/failure logic, not whether Tavily works. So the external
  dependency is faked.
"""

from unittest.mock import MagicMock, patch

from tools.search_tool import NewsSearchTool


def _fake_response(n: int) -> dict:
    """Build a fake Tavily response."""
    return {
        "results": [
            {"title": f"article{i}", "url": f"https://x.com/{i}", "content": "body"}
            for i in range(n)
        ]
    }


@patch("tools.search_tool.TavilyClient")
def test_normal_search_includes_results(mock_client_cls):
    # Make Tavily return 2 articles
    mock_client = MagicMock()
    mock_client.search.return_value = _fake_response(2)
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert "article0" in out
    assert "2 results" in out


@patch("tools.search_tool.TavilyClient")
def test_all_keywords_searched(mock_client_cls):
    # [Review #4 check] 3 keywords must trigger 3 search calls
    mock_client = MagicMock()
    mock_client.search.return_value = _fake_response(1)
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI", "ML", "agents"])

    assert mock_client.search.call_count == 3
    for kw in ["AI", "ML", "agents"]:
        assert f"[keyword: {kw}]" in out


@patch("tools.search_tool.time.sleep")  # skip waiting to speed up the test
@patch("tools.search_tool.TavilyClient")
def test_retry_then_graceful_degradation(mock_client_cls, mock_sleep):
    # If search always raises -> retry 3 times then return empty (no crash)
    mock_client = MagicMock()
    mock_client.search.side_effect = Exception("API down")
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert mock_client.search.call_count == 3   # exactly 3 attempts
    assert "search failed" in out               # exception absorbed, empty result


@patch("tools.search_tool.time.sleep")
@patch("tools.search_tool.TavilyClient")
def test_recovers_after_transient_failure(mock_client_cls, mock_sleep):
    # First 2 attempts fail, 3rd succeeds -> must return results
    mock_client = MagicMock()
    mock_client.search.side_effect = [
        Exception("transient"),
        Exception("transient"),
        _fake_response(1),
    ]
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert mock_client.search.call_count == 3
    assert "article0" in out  # recovered
