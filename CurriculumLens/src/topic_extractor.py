"""
topic_extractor.py
Extracts units and topics from uploaded syllabus documents.
Supports PDF (via PyMuPDF), DOCX, and TXT.
"""

import io
import re
from pathlib import Path
from typing import Optional

from src.preprocessing import clean_syllabus_text


# ── Document text extraction ──────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return "\n".join(pages)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {e}")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode TXT file."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file with supported encodings.")


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Dispatch text extraction based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        text = extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        text = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Please upload PDF, DOCX, or TXT.")

    cleaned = clean_syllabus_text(text)
    if len(cleaned.strip()) < 10:
        raise ValueError(
            "Very little text could be extracted from the document. "
            "If this is a scanned PDF, text extraction is not supported in this version. "
            "Please use a text-based PDF, DOCX, or TXT file."
        )
    return cleaned


# ── Syllabus segmentation ─────────────────────────────────────────────────────

# Explicit unit/module/chapter/block/part/week headings
EXPLICIT_UNIT_PATTERNS = [
    re.compile(r"^\b(unit|module|chapter|block|part|week)\b\s*[:\-\s]*([0-9IVXLCDM]+|[a-z]+)?\b", re.IGNORECASE),
]

# Fallback heading patterns when no explicit units are present
FALLBACK_UNIT_PATTERNS = [
    re.compile(r"^[\d]+[\.\)]\s+[A-Z]"),
    re.compile(r"^\b(topic|theme|lecture|section)\b\s*[:\-\s]*([0-9IVXLCDM]+)?\b", re.IGNORECASE),
]

# Patterns indicating the end of the syllabus curriculum content
# (textbooks, reference bibliographies, lab experiments, grading policies)
STOP_SECTION_PATTERNS = [
    re.compile(r"^(text\s*books?|reference\s*books?|references?|suggested\s*readings?|readings?|bibliography)\s*[:\-]?\s*$", re.IGNORECASE),
    re.compile(r"^(lab\s*work|laboratory\s*work|list\s*of\s*experiments?|practical\s*work|course\s*evaluation|grading\s*policy)\s*[:\-]?\s*$", re.IGNORECASE),
]

# Patterns for topic-level bullet or numbered items
TOPIC_ITEM_PATTERNS = [
    re.compile(r"^[\s]*[-•*◦▪‣–—]\s*(.+)"),          # bullet points
    re.compile(r"^[\s]*\d+[\.\)]\s*(.+)"),          # numbered items e.g. 1. or 1)
    re.compile(r"^[\s]*[a-zA-Z][\.\)]\s*(.+)"),      # lettered items e.g. a) or a.
    re.compile(r"^[\s]*\([a-zA-Z0-9]+\)\s*(.+)"),   # parenthetical items
]

MIN_TOPIC_LENGTH = 3    # characters (e.g. CNN, RNN, PCA, SVM, SQL, Trees)
MAX_TOPIC_LENGTH = 800  # characters


def _is_unit_heading(line: str, patterns: list) -> bool:
    return any(p.match(line.strip()) for p in patterns)


def _extract_bullet_text(line: str) -> Optional[str]:
    for pattern in TOPIC_ITEM_PATTERNS:
        m = pattern.match(line)
        if m:
            return m.group(1).strip()
    return None


def _parse_section_topics(section_lines: list) -> list:
    """Extract individual topic strings from a section's lines."""
    # Check for bullet/numbered items first
    bullet_items = []
    for line in section_lines:
        b = _extract_bullet_text(line)
        if b and len(b) >= MIN_TOPIC_LENGTH:
            bullet_items.append(b)

    if bullet_items:
        # Build enriched chunks: bullet text + its neighbours for context
        enriched = []
        non_bullet = [l for l in section_lines if not any(p.match(l) for p in TOPIC_ITEM_PATTERNS)]
        context_prefix = " ".join(non_bullet[:3]) if non_bullet else ""
        for b in bullet_items:
            chunk = (context_prefix + " " + b).strip() if context_prefix else b
            enriched.append(chunk[:MAX_TOPIC_LENGTH])
        return enriched

    # If no bullet items, inspect line-by-line
    topics = []
    for line in section_lines:
        line_s = line.strip()
        if not line_s or len(line_s) < MIN_TOPIC_LENGTH:
            continue

        # If line contains comma-separated topics (e.g., "Linear Regression, Logistic Regression, Decision Trees")
        if "," in line_s and len(line_s.split(",")) >= 3 and len(line_s) < 300:
            parts = [p.strip() for p in line_s.split(",") if len(p.strip()) >= MIN_TOPIC_LENGTH]
            topics.extend(parts)
        # Semicolon-separated
        elif ";" in line_s and len(line_s.split(";")) >= 2 and len(line_s) < 300:
            parts = [p.strip() for p in line_s.split(";") if len(p.strip()) >= MIN_TOPIC_LENGTH]
            topics.extend(parts)
        else:
            topics.append(line_s[:MAX_TOPIC_LENGTH])

    # Group short adjacent lines into richer chunks so the classifier has enough context
    if topics:
        merged = []
        window = []
        for t in topics:
            window.append(t)
            combined = " ".join(window)
            if len(combined) >= 60 or len(window) >= 4:
                merged.append(combined[:MAX_TOPIC_LENGTH])
                window = []
        if window:
            merged.append(" ".join(window)[:MAX_TOPIC_LENGTH])
        return merged

    return topics


def extract_topics(text: str, doc_name: str = "Document") -> list:
    """
    Parse syllabus text into a list of topic dicts.
    Each dict has: document_name, unit_name, topic_name, topic_text, topic_index
    """
    lines = text.splitlines()
    topics = []
    topic_index = 0

    # Stop scanning at bibliography, reference books, or lab work markers
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if any(stop.match(stripped) for stop in STOP_SECTION_PATTERNS):
            break
        filtered_lines.append(line)

    # Check if explicit unit/module/chapter/block/week headings are present
    has_explicit_units = any(
        any(pat.match(line.strip()) for pat in EXPLICIT_UNIT_PATTERNS)
        for line in filtered_lines
    )
    active_patterns = EXPLICIT_UNIT_PATTERNS if has_explicit_units else FALLBACK_UNIT_PATTERNS

    # --- Pass 1: Unit-heading-based segmentation ---
    unit_sections = []
    section_lines = []
    section_unit = None

    for line in filtered_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _is_unit_heading(stripped, active_patterns):
            if section_unit and section_lines:
                unit_sections.append((section_unit, section_lines))
            section_unit = stripped
            section_lines = []
        else:
            if section_unit:
                section_lines.append(stripped)
            elif not has_explicit_units:
                # If no explicit units exist in the syllabus, collect into General
                section_unit = "General"
                section_lines.append(stripped)

    if section_unit and section_lines:
        unit_sections.append((section_unit, section_lines))

    # If no unit headings matched at all, treat whole text as one section
    if not unit_sections:
        clean_lines = [l.strip() for l in filtered_lines if l.strip()]
        if clean_lines:
            unit_sections = [("General", clean_lines)]

    # --- Pass 2: Extract topics from each section ---
    for unit_name, section in unit_sections:
        section_topics = _parse_section_topics(section)

        for text_chunk in section_topics:
            text_chunk = text_chunk.strip()
            if len(text_chunk) < MIN_TOPIC_LENGTH:
                continue

            words = text_chunk.split()
            name_words = words[:min(12, len(words))]
            topic_name = " ".join(name_words)
            if len(topic_name) < len(text_chunk):
                topic_name += "…"

            topics.append({
                "document_name": doc_name,
                "unit_name": unit_name,
                "topic_name": topic_name,
                "topic_text": text_chunk[:MAX_TOPIC_LENGTH],
                "topic_index": topic_index,
            })
            topic_index += 1

    # Fallback: if still no topics, split by paragraphs or non-empty lines
    if not topics:
        lines_fallback = [line.strip() for line in text.splitlines() if len(line.strip()) >= MIN_TOPIC_LENGTH]
        for idx, line in enumerate(lines_fallback[:50]):
            words = line.split()
            topic_name = " ".join(words[:10]) + ("…" if len(words) > 10 else "")
            topics.append({
                "document_name": doc_name,
                "unit_name": "General",
                "topic_name": topic_name,
                "topic_text": line[:MAX_TOPIC_LENGTH],
                "topic_index": idx,
            })

    return topics


def get_unit_summary(topics: list) -> dict:
    """Return counts of topics per unit."""
    summary = {}
    for t in topics:
        unit = t["unit_name"]
        summary[unit] = summary.get(unit, 0) + 1
    return summary
