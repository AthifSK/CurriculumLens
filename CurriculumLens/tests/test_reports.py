"""
tests/test_reports.py
Tests CSV and PDF report generation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.report_generator import (
    generate_single_csv,
    generate_comparison_csv,
    generate_single_pdf,
    generate_comparison_pdf,
)


SAMPLE_SINGLE_RESULT = {
    "doc_name": "test.txt",
    "total_topics": 3,
    "total_units": 1,
    "avg_topics_per_unit": 3.0,
    "num_clusters": 2,
    "topics": [
        {"topic_index": 0, "unit_name": "Unit 1", "topic_name": "Linear Regression", "cluster": 0, "topic_text": "Linear regression and least squares."},
        {"topic_index": 1, "unit_name": "Unit 1", "topic_name": "Decision Trees", "cluster": 1, "topic_text": "Decision tree induction and pruning."},
        {"topic_index": 2, "unit_name": "Unit 1", "topic_name": "Neural Networks", "cluster": 0, "topic_text": "Feedforward networks and backpropagation."},
    ]
}

SAMPLE_COMPARISON_RESULT = {
    "name_a": "Existing Syllabus",
    "name_b": "Proposed Syllabus",
    "matching": {
        "summary": {
            "total_topics_a": 2,
            "total_topics_b": 2,
            "topics_a_matched": 1,
            "topics_a_partial": 1,
            "topics_a_unmatched": 0,
            "topics_b_unmatched": 0,
        },
        "topics_a_results": [
            {
                "topic": {"topic_name": "Linear Regression", "unit_name": "Unit 1", "topic_index": 0, "topic_text": "..."},
                "best_match": {
                    "topic_b": {"topic_name": "Regression Analysis", "unit_name": "Unit 1", "topic_index": 0, "topic_text": "..."},
                    "predicted_label": "highly_similar",
                    "confidence": 0.87,
                    "cosine_score": 0.65,
                },
                "match_status": "matched",
            }
        ],
        "topics_b_results": []
    }
}


def test_generate_single_csv():
    csv_bytes = generate_single_csv(SAMPLE_SINGLE_RESULT)
    assert isinstance(csv_bytes, bytes)
    content = csv_bytes.decode('utf-8')
    assert 'topic_index' in content
    assert 'Linear Regression' in content


def test_generate_comparison_csv():
    csv_bytes = generate_comparison_csv(SAMPLE_COMPARISON_RESULT)
    assert isinstance(csv_bytes, bytes)
    content = csv_bytes.decode('utf-8')
    assert 'topic_a' in content


def test_generate_single_pdf():
    pdf_bytes = generate_single_pdf(SAMPLE_SINGLE_RESULT)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b'%PDF'


def test_generate_comparison_pdf():
    pdf_bytes = generate_comparison_pdf(SAMPLE_COMPARISON_RESULT)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b'%PDF'
