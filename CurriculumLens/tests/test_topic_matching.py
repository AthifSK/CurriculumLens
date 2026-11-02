"""
tests/test_topic_matching.py
Tests the topic matching logic and single/comparison analysis.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.topic_extractor import extract_topics
from src.single_analysis import analyze_single_syllabus, compute_topic_similarity_matrix


SYLLABUS_A = """
Unit 1: Machine Learning Fundamentals
- Supervised learning: classification and regression
- Unsupervised learning: clustering and dimensionality reduction
- Model evaluation: cross-validation and metrics

Unit 2: Deep Learning
- Neural networks and backpropagation
- Convolutional neural networks for image recognition
"""

SYLLABUS_B = """
Unit 1: Introduction to AI
- Classification algorithms: decision trees and SVM
- Regression analysis and prediction
- Performance metrics: accuracy and F1

Unit 2: Natural Language Processing
- Text preprocessing and tokenization
- Sentiment analysis and text classification
"""


def test_single_analysis_structure():
    topics = extract_topics(SYLLABUS_A, doc_name="test_a.txt")
    result = analyze_single_syllabus(topics, doc_name="test_a.txt")
    assert "total_topics" in result
    assert "total_units" in result
    assert "unit_distribution" in result
    assert "topics" in result
    assert "similarity_pairs" in result


def test_single_analysis_empty():
    result = analyze_single_syllabus([], doc_name="empty.txt")
    assert "error" in result


def test_similarity_matrix_returns_list():
    topics = extract_topics(SYLLABUS_A, doc_name="test.txt")
    pairs = compute_topic_similarity_matrix(topics)
    assert isinstance(pairs, list)
    for p in pairs:
        assert "source" in p
        assert "target" in p
        assert "score" in p
        assert 0 <= p["score"] <= 1


@pytest.mark.skipif(
    not (Path("models/tfidf_vectorizer.joblib").exists() and
         Path("models/syllabus_classifier.joblib").exists()),
    reason="Trained model not found – run train_model.py first"
)
def test_comparison_analysis_structure():
    from src.comparison_analysis import analyze_comparison
    topics_a = extract_topics(SYLLABUS_A, doc_name="a.txt")
    topics_b = extract_topics(SYLLABUS_B, doc_name="b.txt")
    result = analyze_comparison(topics_a, topics_b, "a.txt", "b.txt")
    assert "matching" in result
    assert "summary" in result["matching"]
    summary = result["matching"]["summary"]
    assert "total_topics_a" in summary
    assert "total_topics_b" in summary
    assert "label_distribution" in summary


@pytest.mark.skipif(
    not (Path("models/tfidf_vectorizer.joblib").exists() and
         Path("models/syllabus_classifier.joblib").exists()),
    reason="Trained model not found – run train_model.py first"
)
def test_unmatched_topics_identified():
    from src.comparison_analysis import analyze_comparison
    topics_a = extract_topics(SYLLABUS_A, doc_name="a.txt")
    topics_b = extract_topics(SYLLABUS_B, doc_name="b.txt")
    result = analyze_comparison(topics_a, topics_b, "a.txt", "b.txt")
    b_results = result["matching"]["topics_b_results"]
    statuses = {r["match_status"] for r in b_results}
    # There should be at least one status present
    assert len(statuses) >= 1
    assert all(s in {"matched", "partially_matched", "unmatched"} for s in statuses)
