#!/usr/bin/env python3
"""
evaluate_model.py  –  CurriculumLens
Evaluates the selected model on the held-out test set.
Must be run AFTER train_model.py.

Usage:
    python evaluate_model.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
from scipy.sparse import hstack as sp_hstack
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix
)

from src.data_loader import load_test, CLASS_LABELS, TARGET_COLUMN
from src.preprocessing import build_pair_features

MODELS_DIR = Path("models")
EVALUATION_DIR = Path("evaluation")
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = MODELS_DIR / "syllabus_classifier.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"


def evaluate():
    print("=" * 60)
    print("CurriculumLens – Model Evaluation (Test Set)")
    print("=" * 60)

    if not CLASSIFIER_PATH.exists() or not VECTORIZER_PATH.exists():
        print("\n[ERROR] Model files not found. Run: python train_model.py")
        sys.exit(1)

    # Load model
    print("\n[1/3] Loading model and vectorizer...")
    vectorizer = joblib.load(VECTORIZER_PATH)
    classifier = joblib.load(CLASSIFIER_PATH)

    # Load char vectorizer if present (combined features)
    CHAR_VECTORIZER_PATH = MODELS_DIR / "tfidf_char_vectorizer.joblib"
    char_vectorizer = None
    if CHAR_VECTORIZER_PATH.exists():
        try:
            char_vectorizer = joblib.load(CHAR_VECTORIZER_PATH)
            print("  Char vectorizer loaded (combined word+char features).")
        except Exception:
            pass

    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    print(f"  Model: {metadata.get('model_name', 'Unknown')}")

    # Load test data
    print("\n[2/3] Loading test split...")
    test_df = load_test()
    print(f"  Test examples: {len(test_df)}")

    X_test_raw = build_pair_features(test_df)
    y_test = test_df[TARGET_COLUMN].tolist()

    # Build features – match training pipeline
    X_word = vectorizer.transform(X_test_raw)
    if char_vectorizer is not None:
        X_char = char_vectorizer.transform(X_test_raw)
        X_test = sp_hstack([X_word, X_char])
    else:
        X_test = X_word

    # Evaluate
    print("\n[3/3] Evaluating on test set...")
    y_pred = classifier.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    macro_prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=CLASS_LABELS).tolist()
    report = classification_report(
        y_test, y_pred, labels=CLASS_LABELS, output_dict=True, zero_division=0
    )
    report_text = classification_report(
        y_test, y_pred, labels=CLASS_LABELS, zero_division=0
    )

    print(f"\n  Accuracy        : {acc:.4f}")
    print(f"  Macro F1        : {macro_f1:.4f}")
    print(f"  Macro Precision : {macro_prec:.4f}")
    print(f"  Macro Recall    : {macro_rec:.4f}")
    print(f"\n  Classification Report:\n{report_text}")

    # Save results
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    test_metrics = {
        "split": "test",
        "model": metadata.get("model_name", "Unknown"),
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "confusion_matrix": cm,
        "confusion_matrix_labels": CLASS_LABELS,
        "classification_report": report,
    }

    with open(EVALUATION_DIR / "metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=2)

    with open(EVALUATION_DIR / "classification_report.json", "w") as f:
        json.dump(report, f, indent=2)

    with open(EVALUATION_DIR / "confusion_matrix.json", "w") as f:
        json.dump({"matrix": cm, "labels": CLASS_LABELS}, f, indent=2)

    print(f"\n  Results saved to: {EVALUATION_DIR}/")
    print("=" * 60)
    print("Evaluation complete.")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()
