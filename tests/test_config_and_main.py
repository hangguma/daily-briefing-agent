"""
설정 검증 및 main.py 헬퍼 함수 테스트.
"""

from unittest.mock import patch

import pytest

from config import settings


def test_validate_키없으면_에러():
    # 두 키 모두 비어있으면 ValueError, 메시지에 키 이름 포함
    with patch.object(settings, "ANTHROPIC_API_KEY", ""), \
         patch.object(settings, "TAVILY_API_KEY", ""):
        with pytest.raises(ValueError) as exc:
            settings.validate()
        assert "ANTHROPIC_API_KEY" in str(exc.value)
        assert "TAVILY_API_KEY" in str(exc.value)


def test_validate_키있으면_통과():
    with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-xxx"), \
         patch.object(settings, "TAVILY_API_KEY", "tvly-xxx"):
        # 예외가 발생하지 않아야 함
        settings.validate()


def test_validate_일부키만_있으면_에러():
    # ANTHROPIC만 있고 TAVILY 없으면 → TAVILY만 에러 메시지에
    with patch.object(settings, "ANTHROPIC_API_KEY", "sk-ant-xxx"), \
         patch.object(settings, "TAVILY_API_KEY", ""):
        with pytest.raises(ValueError) as exc:
            settings.validate()
        assert "TAVILY_API_KEY" in str(exc.value)
        assert "ANTHROPIC_API_KEY" not in str(exc.value)


def test_save_report_파일_생성(tmp_path):
    # main.save_report가 .md 파일을 만들고 내용을 쓰는지 검증
    import main

    with patch.object(settings, "OUTPUT_DIR", str(tmp_path)):
        path = main.save_report("# 테스트 브리핑")

    assert path.endswith(".md")
    with open(path, encoding="utf-8") as f:
        assert "테스트 브리핑" in f.read()


def test_parse_args_기본_키워드():
    # 인자 없이 실행하면 기본 키워드 사용
    import main

    with patch("sys.argv", ["main.py"]):
        kws = main.parse_args()
    assert kws == settings.DEFAULT_KEYWORDS


def test_parse_args_최대_5개로_제한():
    # 키워드 7개를 줘도 5개로 잘림 (비용/안정성 보호)
    import main

    args = ["main.py", "--keywords", "a", "b", "c", "d", "e", "f", "g"]
    with patch("sys.argv", args):
        kws = main.parse_args()
    assert len(kws) == 5
