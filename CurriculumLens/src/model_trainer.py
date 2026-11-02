"""
model_trainer.py
Trains Logistic Regression and Linear SVM classifiers on the
syllabus similarity dataset, selects the best model, and saves it.
"""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

# Add parent to path so we can import src modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import load_train, load_val, CLASS_LABELS, TARGET_COLUMN
from src.preprocessing import build_pair_features

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
EVALUATION_DIR = Path(__file__).resolve().parent.parent / "evaluation"

VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = MODELS_DIR / "syllabus_classifier.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"


def build_vectorizer_word() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 3),
        max_features=50000,
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode",
    )


def build_vectorizer_char() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=30000,
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode",
    )


def build_vectorizer() -> TfidfVectorizer:
    """Primary vectorizer used at inference time (word n-grams)."""
    return build_vectorizer_word()


def evaluate_split(model, X, y_true: list, split_name: str) -> dict:
    """Evaluate a model and return metrics dict."""
    y_pred = model.predict(X)

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    macro_prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_true, y_pred, average="macro", zero_division=0)

    report = classification_report(
        y_true, y_pred, labels=CLASS_LABELS, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=CLASS_LABELS).tolist()

    return {
        "split": split_name,
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "classification_report": report,
        "confusion_matrix": cm,
        "confusion_matrix_labels": CLASS_LABELS,
    }


def train():
    print("=" * 60)
    print("CurriculumLens – Model Training")
    print("=" * 60)

    # ── 1. Load data ──────────────────────────────────────────────
    print("\n[1/5] Loading dataset splits...")
    train_df = load_train()
    val_df = load_val()
    print(f"  Train: {len(train_df)} examples")
    print(f"  Val:   {len(val_df)} examples")

    # ── 2. Build paired text ──────────────────────────────────────
    print("\n[2/5] Building paired text representations...")
    X_train_raw = build_pair_features(train_df)
    X_val_raw = build_pair_features(val_df)
    y_train = train_df[TARGET_COLUMN].tolist()
    y_val = val_df[TARGET_COLUMN].tolist()

    # ── 3. Fit TF-IDF on training data ONLY ──────────────────────
    print("\n[3/5] Fitting TF-IDF vectorizers on training data...")

    # Word-level vectorizer (primary)
    vec_word = build_vectorizer_word()
    X_train_word = vec_word.fit_transform(X_train_raw)
    X_val_word   = vec_word.transform(X_val_raw)

    # Char-level vectorizer (supplementary)
    vec_char = build_vectorizer_char()
    X_train_char = vec_char.fit_transform(X_train_raw)
    X_val_char   = vec_char.transform(X_val_raw)

    # Combine word + char features via sparse hstack
    from scipy.sparse import hstack as sp_hstack
    X_train = sp_hstack([X_train_word, X_train_char])
    X_val   = sp_hstack([X_val_word,   X_val_char])

    print(f"  Word vocab:  {len(vec_word.vocabulary_)}")
    print(f"  Char vocab:  {len(vec_char.vocabulary_)}")
    print(f"  Combined feature matrix: {X_train.shape}")

    # ── 4. Train candidates ───────────────────────────────────────
    print("\n[4/5] Training candidate classifiers...")
    print("  Note: class_weight='balanced' used to handle class imbalance.")

    # Logistic Regression – balanced weights, try C values
    best_lr, best_lr_f1 = None, -1
    for C in [0.01, 0.1, 0.5, 1.0, 3.0, 10.0]:
        m = LogisticRegression(
            max_iter=3000, C=C, solver="lbfgs",
            class_weight="balanced", random_state=42
        )
        m.fit(X_train, y_train)
        f1 = f1_score(y_val, m.predict(X_val), average="macro", zero_division=0)
        if f1 > best_lr_f1:
            best_lr_f1, best_lr = f1, m
    lr = best_lr
    print(f"  Logistic Regression best – Val Macro-F1: {best_lr_f1:.4f}")

    # Linear SVM – balanced weights, calibrated for probabilities
    best_svm, best_svm_f1 = None, -1
    for C in [0.01, 0.1, 0.5, 1.0, 3.0]:
        svm_base = LinearSVC(C=C, max_iter=5000, class_weight="balanced", random_state=42)
        svm_c = CalibratedClassifierCV(svm_base, cv=3)
        svm_c.fit(X_train, y_train)
        f1 = f1_score(y_val, svm_c.predict(X_val), average="macro", zero_division=0)
        if f1 > best_svm_f1:
            best_svm_f1, best_svm = f1, svm_c
    svm = best_svm
    print(f"  Linear SVM best         – Val Macro-F1: {best_svm_f1:.4f}")

    # ── 5. Compare on validation set ──────────────────────────────
    print("\n[5/5] Comparing models on validation set...")
    lr_val  = evaluate_split(lr,  X_val, y_val, "validation")
    svm_val = evaluate_split(svm, X_val, y_val, "validation")

    print(f"\n  Logistic Regression  – Val Macro-F1: {lr_val['macro_f1']:.4f}  Acc: {lr_val['accuracy']:.4f}")
    print(f"  Linear SVM           – Val Macro-F1: {svm_val['macro_f1']:.4f}  Acc: {svm_val['accuracy']:.4f}")

    # Select best model by macro-F1 on validation set
    if lr_val["macro_f1"] >= svm_val["macro_f1"]:
        best_model = lr
        best_name = "Logistic Regression"
        best_val_metrics = lr_val
    else:
        best_model = svm
        best_name = "Linear SVM (Calibrated)"
        best_val_metrics = svm_val

    print(f"\n  [SELECTED]: {best_name}")

    # ── Save model and vectorizers ────────────────────────────────
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vec_word, VECTORIZER_PATH)
    joblib.dump(vec_char, MODELS_DIR / "tfidf_char_vectorizer.joblib")
    joblib.dump(best_model, CLASSIFIER_PATH)
    print(f"\n  Word vectorizer saved → {VECTORIZER_PATH}")
    print(f"  Char vectorizer saved → {MODELS_DIR / 'tfidf_char_vectorizer.joblib'}")
    print(f"  Classifier saved      → {CLASSIFIER_PATH}")

    # Save metadata
    metadata = {
        "model_name": best_name,
        "class_labels": CLASS_LABELS,
        "vectorizer_params": {
            "word_vectorizer": {
                "analyzer": "word",
                "ngram_range": list(vec_word.ngram_range),
                "max_features": vec_word.max_features,
                "sublinear_tf": bool(vec_word.sublinear_tf),
            },
            "char_vectorizer": {
                "analyzer": "char_wb",
                "ngram_range": [3, 5],
                "max_features": 30000,
                "sublinear_tf": True,
            },
        },
        "selection_criterion": "macro_f1_on_validation",
        "candidate_val_metrics": {
            "logistic_regression": {
                "macro_f1": lr_val["macro_f1"],
                "accuracy": lr_val["accuracy"],
            },
            "linear_svm": {
                "macro_f1": svm_val["macro_f1"],
                "accuracy": svm_val["accuracy"],
            },
        },
        "selected_model_val_metrics": {
            "macro_f1": best_val_metrics["macro_f1"],
            "accuracy": best_val_metrics["accuracy"],
            "macro_precision": best_val_metrics["macro_precision"],
            "macro_recall": best_val_metrics["macro_recall"],
        },
        "train_size": len(train_df),
        "val_size": len(val_df),
        "data_origin": "synthetic",
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved  → {METADATA_PATH}")

    # Save validation evaluation details
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    val_eval = {
        "logistic_regression": lr_val,
        "linear_svm": svm_val,
        "selected_model": best_name,
    }
    with open(EVALUATION_DIR / "validation_comparison.json", "w") as f:
        json.dump(val_eval, f, indent=2)

    print("\n" + "=" * 60)
    print("Training complete. Run evaluate_model.py for test evaluation.")
    print("=" * 60)

    return vec_word, vec_char, best_model, best_name


if __name__ == "__main__":
    train()
