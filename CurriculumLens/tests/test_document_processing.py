"""
tests/test_document_processing.py
Tests document text extraction and topic extraction.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.topic_extractor import (
    extract_text_from_txt,
    extract_topics,
    get_unit_summary,
)


SAMPLE_SYLLABUS = """
Unit 1: Introduction to Machine Learning
- Supervised vs unsupervised learning
- Common applications and problem types
- Data preprocessing and feature engineering

Unit 2: Classification Algorithms
- Logistic regression for binary classification
- Decision trees and random forests
- Support vector machines and kernel methods

Unit 3: Model Evaluation
- Train/validation/test splits
- Cross-validation techniques
- Accuracy, precision, recall, F1-score
"""


def test_extract_text_from_txt_utf8():
    content = "Hello, this is a test syllabus.\nSecond line."
    text = extract_text_from_txt(content.encode("utf-8"))
    assert "Hello" in text
    assert "Second line" in text


def test_extract_text_from_txt_latin1():
    content = "Caf\xe9 introduction to NLP"
    text = extract_text_from_txt(content.encode("latin-1"))
    assert text  # Should not crash


def test_extract_topics_basic():
    topics = extract_topics(SAMPLE_SYLLABUS, doc_name="test.txt")
    assert len(topics) > 0
    for t in topics:
        assert "topic_text" in t
        assert "topic_name" in t
        assert "unit_name" in t
        assert "topic_index" in t


def test_extract_topics_finds_units():
    topics = extract_topics(SAMPLE_SYLLABUS, doc_name="test.txt")
    units = {t["unit_name"] for t in topics}
    # Should find some unit headings
    assert len(units) >= 1


def test_get_unit_summary():
    topics = extract_topics(SAMPLE_SYLLABUS, doc_name="test.txt")
    summary = get_unit_summary(topics)
    assert isinstance(summary, dict)
    for k, v in summary.items():
        assert isinstance(v, int)
        assert v > 0


def test_empty_document_raises():
    from src.topic_extractor import extract_text
    with pytest.raises(ValueError):
        extract_text("empty.txt", b"")


def test_unsupported_extension_raises():
    from src.topic_extractor import extract_text
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text("file.xyz", b"some content")


def test_short_text_raises():
    from src.topic_extractor import extract_text
    with pytest.raises(ValueError):
        extract_text("tiny.txt", b"Hi")
