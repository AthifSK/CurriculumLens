"""
preprocessing.py
Text normalization and feature construction for the syllabus classifier.
"""

import re
import unicodedata

SEP_TOKEN = " [SEP] "


def normalize_text(text: str) -> str:
    """
    Normalize a text string for NLP processing.
    - Lowercase
    - Normalize unicode
    - Strip extra whitespace
    - Remove non-printable characters
    """
    if not isinstance(text, str):
        text = str(text)
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)
    # Lowercase
    text = text.lower()
    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7e\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_pair_text(text_a: str, text_b: str) -> str:
    """
    Build a combined text representation from a topic pair.
    Uses a separator token between the two texts.
    """
    return normalize_text(text_a) + SEP_TOKEN + normalize_text(text_b)


def build_pair_features(df):
    """
    Given a DataFrame with text_a and text_b columns,
    return a list of combined pair strings.
    """
    return [
        build_pair_text(row["text_a"], row["text_b"])
        for _, row in df.iterrows()
    ]


def clean_syllabus_text(raw_text: str) -> str:
    """
    Clean extracted syllabus text for display and analysis.
    Preserves headings and meaningful structure.
    """
    if not raw_text:
        return ""
    # Remove excessive blank lines (keep max 2 newlines)
    text = re.sub(r"\n{3,}", "\n\n", raw_text)
    # Remove leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    # Remove lines that are purely special characters or numbers
    cleaned = []
    for line in lines:
        if re.match(r"^[\s\-_=*#.]+$", line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()
