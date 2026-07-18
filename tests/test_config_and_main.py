"""
Tests for settings validation and main.py helper functions.
"""

from unittest.mock import patch

import pytest

from config import settings


def test_validate_errors_when_no_keys():
    # Both keys empty -> ValueError mentioning both key names
    with patch.object(settings, "ANTHROPIC_API_KEY", ""), \
         patch.object(settings, "TAVILY_API_KEY", ""):
        with pytest.raises(ValueError) as exc:
            settings.validate()
        assert "ANTHROPIC_API_KEY" in str(exc.value)
        assert "TAVILY_API_KEY" in str(exc.value)


def test_validate_passes_with_keys():
    with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-xxx"), \
         patch.object(settings, "TAVILY_API_KEY", "tvly-xxx"):
        # Must not raise
        settings.validate()


def test_validate_errors_when_partial_keys():
    # ANTHROPIC present, TAVILY missing -> only TAVILY in the message
    with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-xxx"), \
         patch.object(settings, "TAVILY_API_KEY", ""):
        with pytest.raises(ValueError) as exc:
            settings.validate()
        assert "TAVILY_API_KEY" in str(exc.value)
        assert "ANTHROPIC_API_KEY" not in str(exc.value)


def test_save_report_creates_file(tmp_path):
    # main.save_report should create a .md file and write its content
    import main

    with patch.object(settings, "OUTPUT_DIR", str(tmp_path)):
        path = main.save_report("# Test briefing")

    assert path.endswith(".md")
    with open(path, encoding="utf-8") as f:
        assert "Test briefing" in f.read()


def test_parse_args_default_keywords():
    # No args -> use default keywords
    import main

    with patch("sys.argv", ["main.py"]):
        kws = main.parse_args()
    assert kws == settings.DEFAULT_KEYWORDS


def test_parse_args_caps_at_5():
    # 7 keywords -> capped at 5 (cost/stability guardrail)
    import main

    args = ["main.py", "--keywords", "a", "b", "c", "d", "e", "f", "g"]
    with patch("sys.argv", args):
        kws = main.parse_args()
    assert len(kws) == 5


def test_parse_args_accepts_korean_and_english():
    # Keywords may be Korean, English, or mixed (incl. spaces in quotes)
    import main

    args = ["main.py", "--keywords", "인공지능", "AI startup", "machine learning"]
    with patch("sys.argv", args):
        kws = main.parse_args()
    assert kws == ["인공지능", "AI startup", "machine learning"]


def test_search_conditions_footer_includes_all():
    # Footer must include keywords + all search settings
    import main

    footer = main.format_search_conditions(["AI", "agents"])
    assert "Search conditions" in footer
    assert "`AI`" in footer and "`agents`" in footer
    assert str(settings.RESULTS_PER_KEYWORD) in footer
    assert str(settings.TOP_N_ARTICLES) in footer
    assert str(settings.SEARCH_DAYS) in footer
    assert settings.SEARCH_TOPIC in footer
    assert settings.SEARCH_DEPTH in footer
    assert settings.LLM_MODEL in footer
