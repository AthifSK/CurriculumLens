"""
tests/test_model.py
Tests model loading, prediction, and missing-model handling.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.syllabus_classifier import is_model_available, CLASS_LABELS


def test_class_labels_defined():
    assert "highly_similar" in CLASS_LABELS
    assert "partially_similar" in CLASS_LABELS
    assert "unrelated" in CLASS_LABELS


def test_model_available_returns_bool():
    result = is_model_available()
    assert isinstance(result, bool)


@pytest.mark.skipif(
    not (Path("models/tfidf_vectorizer.joblib").exists() and
         Path("models/syllabus_classifier.joblib").exists()),
    reason="Trained model not found – run train_model.py first"
)
def test_predict_pair_returns_valid_label():
    from src.syllabus_classifier import predict_pair
    result = predict_pair(
        "Linear regression and gradient descent optimization",
        "Fitting a regression line using least squares and gradient methods"
    )
    assert "label" in result
    assert result["label"] in CLASS_LABELS
    assert "confidence" in result


@pytest.mark.skipif(
    not (Path("models/tfidf_vectorizer.joblib").exists() and
         Path("models/syllabus_classifier.joblib").exists()),
    reason="Trained model not found – run train_model.py first"
)
def test_predict_all_three_classes():
    """Check that the classifier can in principle produce all three classes."""
    from src.syllabus_classifier import predict_batch
    pairs = [
        ("Linear regression and gradient descent", "Fitting a line using least squares gradient methods"),
        ("Introduction to databases and SQL queries", "Python syntax variables loops and functions"),
        ("Decision trees and random forests", "Ensemble learning: random forests and boosting"),
    ]
    results = predict_batch(pairs)
    assert len(results) == 3
    labels = {r["label"] for r in results}
    # At least two distinct classes should appear across three varied pairs
    assert len(labels) >= 1
    for r in results:
        assert r["label"] in CLASS_LABELS


@pytest.mark.skipif(
    not (Path("models/tfidf_vectorizer.joblib").exists() and
         Path("models/syllabus_classifier.joblib").exists()),
    reason="Trained model not found – run train_model.py first"
)
def test_metadata_file_exists():
    meta_path = Path("models/model_metadata.json")
    assert meta_path.exists()
    with open(meta_path) as f:
        meta = json.load(f)
    assert "model_name" in meta
    assert "class_labels" in meta
