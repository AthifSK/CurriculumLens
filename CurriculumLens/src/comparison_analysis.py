"""
comparison_analysis.py
Orchestrates two-syllabus comparison workflow.
"""

from src.topic_extractor import get_unit_summary
from src.topic_matcher import match_topics


def analyze_comparison(topics_a: list, topics_b: list, name_a: str, name_b: str) -> dict:
    """
    Full two-syllabus comparison pipeline.
    """
    if not topics_a:
        return {"error": f"No topics extracted from '{name_a}'."}
    if not topics_b:
        return {"error": f"No topics extracted from '{name_b}'."}

    unit_summary_a = get_unit_summary(topics_a)
    unit_summary_b = get_unit_summary(topics_b)

    matching_result = match_topics(topics_a, topics_b)

    return {
        "name_a": name_a,
        "name_b": name_b,
        "unit_distribution_a": unit_summary_a,
        "unit_distribution_b": unit_summary_b,
        "matching": matching_result,
    }
