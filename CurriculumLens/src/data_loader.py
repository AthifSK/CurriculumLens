"""
data_loader.py
Loads and validates the syllabus similarity dataset splits.
"""

import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "final_syllabus_similarity_dataset"

REQUIRED_COLUMNS = {"text_a", "text_b", "label"}
TEXT_COLUMNS = ["text_a", "text_b"]
TARGET_COLUMN = "label"
CLASS_LABELS = ["highly_similar", "partially_similar", "unrelated"]


def _load_split(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {path}\n"
            f"Please place the dataset files in: {DATA_DIR}"
        )
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {filename}: {missing}")
    return df


def load_train() -> pd.DataFrame:
    """Load the training split."""
    return _load_split("train.csv")


def load_val() -> pd.DataFrame:
    """Load the validation split."""
    return _load_split("val.csv")


def load_test() -> pd.DataFrame:
    """Load the test split."""
    return _load_split("test.csv")


def load_all() -> pd.DataFrame:
    """Load the complete dataset."""
    return _load_split("final_dataset.csv")


def get_dataset_info() -> dict:
    """Return a summary of the dataset."""
    try:
        df = load_all()
        train = load_train()
        val = load_val()
        test = load_test()
        return {
            "total_examples": len(df),
            "train_size": len(train),
            "val_size": len(val),
            "test_size": len(test),
            "class_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
            "classes": CLASS_LABELS,
            "data_origin": df["data_origin"].value_counts().to_dict() if "data_origin" in df.columns else {},
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    info = get_dataset_info()
    for k, v in info.items():
        print(f"{k}: {v}")
