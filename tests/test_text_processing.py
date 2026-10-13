import pytest

from app.services.text_processing import clean_text, split_text

def test_clean_text_removes_extra_spaces():
    original = "AI    Doc\tAssistant"

    result = clean_text(original)

    assert result == "AI Doc Assistant"


def test_clean_text_normalizes_line_breaks():
    original = "第一段\r\n第二段\r第三段"

    result = clean_text(original)

    assert result == "第一段\n第二段\n第三段"


def test_clean_text_removes_extra_blank_lines():
    original = "第一段\n\n\n\n第二段"

    result = clean_text(original)

    assert result == "第一段\n\n第二段"


def test_clean_text_strips_each_line():
    original = "  第一行  \n  第二行  "

    result = clean_text(original)

    assert result == "第一行\n第二行"




def test_split_text_creates_overlapping_chunks():
    text = "abcdefghij"

    result = split_text(
        text,
        chunk_size=4,
        overlap=1,
    )

    assert result == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_split_text_returns_single_short_chunk():
    result = split_text(
        "短文本",
        chunk_size=100,
        overlap=10,
    )

    assert result == ["短文本"]


def test_split_text_returns_empty_list():
    result = split_text(
        "   ",
        chunk_size=100,
        overlap=10,
    )

    assert result == []


def test_split_text_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        split_text(
            "测试文本",
            chunk_size=100,
            overlap=100,
        )
