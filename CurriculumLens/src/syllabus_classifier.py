"""
syllabus_classifier.py
Loads the trained model and provides prediction utilities.
Uses combined word + char TF-IDF features for better accuracy.
"""

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
VECTORIZER_PATH      = MODELS_DIR / "tfidf_vectorizer.joblib"
CHAR_VECTORIZER_PATH = MODELS_DIR / "tfidf_char_vectorizer.joblib"
CLASSIFIER_PATH      = MODELS_DIR / "syllabus_classifier.joblib"
METADATA_PATH        = MODELS_DIR / "model_metadata.json"

CLASS_LABELS = ["highly_similar", "partially_similar", "unrelated"]

_vectorizer      = None
_char_vectorizer = None
_classifier      = None
_metadata        = None
_use_char        = False   # set True once char vectorizer loads successfully


def _load_models():
    global _vectorizer, _char_vectorizer, _classifier, _metadata, _use_char

    if _vectorizer is None:
        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"Vectorizer not found at {VECTORIZER_PATH}. "
                "Please run: python train_model.py"
            )
        _vectorizer = joblib.load(VECTORIZER_PATH)

    if _char_vectorizer is None and CHAR_VECTORIZER_PATH.exists():
        try:
            _char_vectorizer = joblib.load(CHAR_VECTORIZER_PATH)
            _use_char = True
        except Exception:
            _use_char = False

    if _classifier is None:
        if not CLASSIFIER_PATH.exists():
            raise FileNotFoundError(
                f"Classifier not found at {CLASSIFIER_PATH}. "
                "Please run: python train_model.py"
            )
        _classifier = joblib.load(CLASSIFIER_PATH)

    if _metadata is None and METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)


def _build_features(texts: list):
    """Build combined word + char feature matrix for a list of texts."""
    X_word = _vectorizer.transform(texts)
    if _use_char and _char_vectorizer is not None:
        from scipy.sparse import hstack as sp_hstack
        X_char = _char_vectorizer.transform(texts)
        return sp_hstack([X_word, X_char])
    return X_word


def is_model_available() -> bool:
    return VECTORIZER_PATH.exists() and CLASSIFIER_PATH.exists()


def get_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as f:
        return json.load(f)


def predict_pair(text_a: str, text_b: str) -> dict:
    """
    Predict the similarity class for a pair of syllabus texts.
    Returns: { label, confidence, probabilities }
    """
    from src.preprocessing import build_pair_text
    _load_models()

    combined = build_pair_text(text_a, text_b)
    X = _build_features([combined])

    label = _classifier.predict(X)[0]

    try:
        proba     = _classifier.predict_proba(X)[0]
        classes   = _classifier.classes_
        prob_dict = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}
        confidence = round(float(max(proba)), 4)
    except Exception:
        prob_dict  = {lbl: None for lbl in CLASS_LABELS}
        confidence = None

    return {
        "label":         label,
        "confidence":    confidence,
        "probabilities": prob_dict,
    }


def predict_batch(text_pairs: list) -> list:
    """
    Predict similarity for a list of (text_a, text_b) tuples.
    Returns a list of prediction dicts.
    """
    from src.preprocessing import build_pair_text
    _load_models()

    combined = [build_pair_text(a, b) for a, b in text_pairs]
    X = _build_features(combined)

    labels = _classifier.predict(X)

    try:
        probas  = _classifier.predict_proba(X)
        classes = _classifier.classes_
    except Exception:
        probas  = None
        classes = CLASS_LABELS

    results = []
    for i, label in enumerate(labels):
        if probas is not None:
            proba     = probas[i]
            prob_dict = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}
            confidence = round(float(max(proba)), 4)
        else:
            prob_dict  = {lbl: None for lbl in CLASS_LABELS}
            confidence = None

        results.append({
            "label":         label,
            "confidence":    confidence,
            "probabilities": prob_dict,
        })
    return results
