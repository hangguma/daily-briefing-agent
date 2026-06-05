"""
검색 도구 단위 테스트.

실제 Tavily API를 호출하지 않고 TavilyClient를 모킹(mock)합니다.
왜 이렇게 하나요?
- 외부 API에 의존하는 테스트는 느리고, 네트워크/요금 문제로 불안정합니다.
- 우리가 검증할 것은 "Tavily가 잘 동작하는가"가 아니라
  "우리의 재시도/실패 처리 로직이 올바른가"입니다. 그래서 외부는 가짜로 둡니다.
"""

from unittest.mock import MagicMock, patch

from tools.search_tool import NewsSearchTool


def _fake_response(n: int) -> dict:
    """가짜 Tavily 응답 생성."""
    return {
        "results": [
            {"title": f"기사{i}", "url": f"https://x.com/{i}", "content": "내용"}
            for i in range(n)
        ]
    }


@patch("tools.search_tool.TavilyClient")
def test_정상_검색_결과_포함(mock_client_cls):
    # Tavily가 기사 2건을 반환하도록 설정
    mock_client = MagicMock()
    mock_client.search.return_value = _fake_response(2)
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert "기사0" in out
    assert "검색 결과 2건" in out


@patch("tools.search_tool.TavilyClient")
def test_모든_키워드_빠짐없이_검색(mock_client_cls):
    # [Review #4 검증] 키워드 3개를 주면 search가 3번 호출되어야 함
    mock_client = MagicMock()
    mock_client.search.return_value = _fake_response(1)
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI", "ML", "agents"])

    assert mock_client.search.call_count == 3
    for kw in ["AI", "ML", "agents"]:
        assert f"[키워드: {kw}]" in out


@patch("tools.search_tool.time.sleep")  # 테스트 속도를 위해 대기 제거
@patch("tools.search_tool.TavilyClient")
def test_실패시_재시도_후_graceful_degradation(mock_client_cls, mock_sleep):
    # search가 항상 예외를 던지면 → 3회 재시도 후 빈 결과 반환 (크래시 X)
    mock_client = MagicMock()
    mock_client.search.side_effect = Exception("API 다운")
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert mock_client.search.call_count == 3   # 정확히 3회 시도
    assert "검색 실패" in out                     # 예외를 흡수하고 빈 결과


@patch("tools.search_tool.time.sleep")
@patch("tools.search_tool.TavilyClient")
def test_일시적_실패_후_복구(mock_client_cls, mock_sleep):
    # 첫 2회 실패, 3회째 성공 → 결과를 정상 반환해야 함
    mock_client = MagicMock()
    mock_client.search.side_effect = [
        Exception("일시 오류"),
        Exception("일시 오류"),
        _fake_response(1),
    ]
    mock_client_cls.return_value = mock_client

    tool = NewsSearchTool()
    out = tool._run(keywords=["AI"])

    assert mock_client.search.call_count == 3
    assert "기사0" in out  # 복구 성공
