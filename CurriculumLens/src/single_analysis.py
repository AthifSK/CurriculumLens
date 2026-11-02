"""
single_analysis.py
Performs single-syllabus analysis: topic extraction, unit distribution,
internal curriculum coherence, cross-unit integration, and structural metrics.
"""

import math
from typing import List

from src.topic_extractor import get_unit_summary
from src.topic_matcher import cosine_similarity_tfidf


def compute_topic_similarity_matrix(topics: list) -> list:
    """
    Compute cosine-based similarity between all topic pairs within one syllabus.
    Returns a list of {source, target, score, label_a, label_b}.
    """
    threshold = 0.15
    pairs = []
    n = len(topics)
    for i in range(n):
        for j in range(i + 1, n):
            score = cosine_similarity_tfidf(topics[i]["topic_text"], topics[j]["topic_text"])
            if score >= threshold:
                pairs.append({
                    "source": topics[i]["topic_index"],
                    "target": topics[j]["topic_index"],
                    "score": round(score, 4),
                    "label_a": topics[i]["topic_name"],
                    "label_b": topics[j]["topic_name"],
                })
    return pairs


def analyze_single_syllabus(topics: list, doc_name: str) -> dict:
    """
    Complete single-syllabus analysis pipeline.
    Calculates internal curriculum coherence, cross-unit integration,
    and structural percentage metrics without clustering graphs.
    """
    if not topics:
        return {
            "error": "No topics could be extracted from the document.",
            "doc_name": doc_name,
        }

    n_topics = len(topics)
    unit_summary = get_unit_summary(topics)
    n_units = len(unit_summary)

    # ── Internal Pairwise Topic Analysis ──────────────────────────
    topic_relations = []
    connected_count = 0
    partial_count = 0
    standalone_count = 0
    cross_unit_count = 0

    for i, ta in enumerate(topics):
        best_sim = 0.0
        best_tb = None
        for j, tb in enumerate(topics):
            if i == j:
                continue
            sim = cosine_similarity_tfidf(ta["topic_text"], tb["topic_text"])
            if sim > best_sim:
                best_sim = sim
                best_tb = tb

        is_cross = bool(best_tb and ta["unit_name"] != best_tb["unit_name"] and best_sim >= 0.14)

        if best_sim >= 0.25:
            relation_level = "strong"
            connected_count += 1
            if is_cross:
                cross_unit_count += 1
        elif best_sim >= 0.14:
            relation_level = "moderate"
            partial_count += 1
            if is_cross:
                cross_unit_count += 1
        else:
            relation_level = "standalone"
            standalone_count += 1

        topic_relations.append({
            "topic_index": ta["topic_index"],
            "unit_name": ta["unit_name"],
            "topic_name": ta["topic_name"],
            "best_related_topic": best_tb["topic_name"] if best_tb else "—",
            "best_related_unit": best_tb["unit_name"] if best_tb else "—",
            "similarity_score": round(best_sim, 3),
            "relation_level": relation_level,
            "is_cross_unit": is_cross,
        })

    # ── High-Level Percentage Metrics ─────────────────────────────
    pct_connected = round(100.0 * connected_count / max(n_topics, 1), 1)
    pct_partial = round(100.0 * partial_count / max(n_topics, 1), 1)
    pct_standalone = round(100.0 * standalone_count / max(n_topics, 1), 1)
    pct_cross_unit = round(100.0 * cross_unit_count / max(n_topics, 1), 1)

    # Curriculum Coherence: fraction of topics that connect or reinforce other concepts
    coherence_pct = round(100.0 * (connected_count + 0.5 * partial_count) / max(n_topics, 1), 1)

    similarity_pairs = compute_topic_similarity_matrix(topics)

    return {
        "doc_name": doc_name,
        "total_topics": n_topics,
        "total_units": n_units,
        "unit_distribution": unit_summary,
        "topics": topic_relations,
        "similarity_pairs": similarity_pairs,
        "avg_topics_per_unit": round(n_topics / max(1, n_units), 2),
        "coherence_percentage": coherence_pct,
        "pct_connected": pct_connected,
        "pct_partial": pct_partial,
        "pct_standalone": pct_standalone,
        "pct_cross_unit": pct_cross_unit,
        "connected_count": connected_count,
        "partial_count": partial_count,
        "standalone_count": standalone_count,
        "cross_unit_count": cross_unit_count,
    }
