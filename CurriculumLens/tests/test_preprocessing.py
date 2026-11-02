"""
tests/test_preprocessing.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocessing import normalize_text, build_pair_text, clean_syllabus_text


def test_normalize_text_lowercase():
    assert normalize_text("Hello World") == "hello world"


def test_normalize_text_strips_whitespace():
    assert normalize_text("  hello   world  ") == "hello world"


def test_normalize_text_handles_non_string():
    assert isinstance(normalize_text(42), str)


def test_build_pair_text_contains_sep():
    result = build_pair_text("Text A content", "Text B content")
    assert "[SEP]" in result
    assert "text a content" in result
    assert "text b content" in result


def test_clean_syllabus_text_removes_blank_lines():
    raw = "Title\n\n\n\nContent"
    cleaned = clean_syllabus_text(raw)
    assert "\n\n\n" not in cleaned


def test_clean_syllabus_text_handles_empty():
    assert clean_syllabus_text("") == ""


def test_clean_syllabus_text_handles_none():
    assert clean_syllabus_text(None) == ""
