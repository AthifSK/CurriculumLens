"""
topic_matcher.py
Implements topic pair matching between two syllabi using the trained classifier
and calibrated semantic retrieval for high-accuracy curriculum comparison.
"""

import math
from typing import List, Optional


def cosine_similarity_tfidf(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using normalized term frequencies.
    Robustly handles subtopic vocabulary differences.
    """
    from src.preprocessing import normalize_text
    a = [w for w in normalize_text(text_a).split() if len(w) > 1]
    b = [w for w in normalize_text(text_b).split() if len(w) > 1]
    if not a or not b:
        return 0.0

    def tf(words):
        d = {}
        for w in words:
            d[w] = d.get(w, 0) + 1
        return d

    tf_a = tf(a)
    tf_b = tf(b)

    common = set(tf_a) & set(tf_b)
    if not common:
        return 0.0

    dot = sum(tf_a[w] * tf_b[w] for w in common)
    norm_a = math.sqrt(sum(v * v for v in tf_a.values()))
    norm_b = math.sqrt(sum(v * v for v in tf_b.values()))
    return dot / (norm_a * norm_b) if (norm_a and norm_b) else 0.0


RETRIEVAL_TOP_K = 10


def _rank_candidates(topic_a: dict, topics_b: list) -> list:
    """
    Rank topics_b by cosine similarity to topic_a.
    Returns list of (score, topic_b_dict) sorted descending.
    """
    scored = []
    for tb in topics_b:
        score = cosine_similarity_tfidf(topic_a["topic_text"], tb["topic_text"])
        scored.append((score, tb))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def match_topics(topics_a: list, topics_b: list) -> dict:
    """
    Compare all topics in syllabus A against topics in syllabus B.
    Returns a structured result with classifications for every candidate pair.
    """
    from src.syllabus_classifier import predict_batch, is_model_available

    if not is_model_available():
        raise RuntimeError(
            "Trained model not found. Please run: python train_model.py"
        )

    # ── Build candidate pairs ─────────────────────────────────────
    all_pairs = []
    pair_map = {}
    pair_set = set()

    FULL_CROSS_LIMIT = 400
    do_full_cross = (len(topics_a) * len(topics_b)) <= FULL_CROSS_LIMIT

    for ta in topics_a:
        ranked = _rank_candidates(ta, topics_b)
        candidates = ranked if do_full_cross else ranked[:RETRIEVAL_TOP_K]

        indices = []
        for score, tb in candidates:
            key = (ta["topic_index"], tb["topic_index"])
            if key not in pair_set:
                pair_set.add(key)
                all_pairs.append((ta, tb, score))
                indices.append(len(all_pairs) - 1)
            else:
                for idx, p in enumerate(all_pairs):
                    if p[0]["topic_index"] == ta["topic_index"] and p[1]["topic_index"] == tb["topic_index"]:
                        indices.append(idx)
                        break
        pair_map[ta["topic_index"]] = indices

    # ── Batch classify all candidate pairs ────────────────────────
    text_pairs = [(p[0]["topic_text"], p[1]["topic_text"]) for p in all_pairs]
    predictions = predict_batch(text_pairs) if text_pairs else []

    # ── Aggregate and calibrate results ───────────────────────────
    classified_pairs = []
    for i, (ta, tb, cos_score) in enumerate(all_pairs):
        pred = predictions[i] if i < len(predictions) else {
            "label": "unrelated", "confidence": 0.0, "probabilities": {}
        }
        probs = pred.get("probabilities") or {}
        p_high = probs.get("highly_similar") or 0.0
        p_part = probs.get("partially_similar") or 0.0
        p_unrel = probs.get("unrelated") or 0.0

        # Calibrated classification
        if cos_score >= 0.35 or (cos_score >= 0.22 and pred["label"] == "highly_similar"):
            calibrated_label = "highly_similar"
            calibrated_conf = max(round(cos_score, 4), pred["confidence"] or 0.80)
        elif (0.20 <= cos_score < 0.35) or (cos_score >= 0.14 and (p_high + p_part) >= 0.50):
            calibrated_label = "partially_similar"
            calibrated_conf = max(round(cos_score, 4), pred["confidence"] or 0.65)
        else:
            calibrated_label = "unrelated"
            calibrated_conf = pred["confidence"] or round(1.0 - cos_score, 4)

        classified_pairs.append({
            "topic_a": ta,
            "topic_b": tb,
            "cosine_score": round(cos_score, 4),
            "predicted_label": calibrated_label,
            "confidence": calibrated_conf,
            "probabilities": probs,
        })

    # ── Per-topic best matches (Syllabus A perspective) ───────────
    a_results = []
    for ta in topics_a:
        idx_list = pair_map.get(ta["topic_index"], [])
        candidates = [classified_pairs[i] for i in idx_list]

        # Rank candidates: prioritize candidates with genuine lexical & semantic overlap
        def score_candidate(cp):
            cos = cp["cosine_score"]
            probs = cp.get("probabilities") or {}
            p_high = probs.get("highly_similar") or 0.0
            p_part = probs.get("partially_similar") or 0.0
            p_unrel = probs.get("unrelated") or 0.0
            return cos * 0.70 + (p_high * 1.0 + p_part * 0.5 - p_unrel * 0.3) * 0.30

        candidates.sort(key=score_candidate, reverse=True)

        best = candidates[0] if candidates else None
        if best:
            lbl = best["predicted_label"]
            cos = best["cosine_score"]
            probs = best.get("probabilities") or {}
            p_high = probs.get("highly_similar") or 0.0
            p_part = probs.get("partially_similar") or 0.0

            if cos >= 0.35 or (cos >= 0.22 and lbl == "highly_similar"):
                match_status = "matched"
            elif (0.20 <= cos < 0.35) or (cos >= 0.14 and (p_high + p_part) >= 0.50):
                match_status = "partially_matched"
            else:
                match_status = "unmatched"
        else:
            match_status = "unmatched"

        a_results.append({
            "topic": ta,
            "best_match": best,
            "match_status": match_status,
            "all_candidates": candidates[:3],
        })

    # ── Per-topic best matches (Syllabus B perspective) ───────────
    # For each B topic, find its best matching A topic to detect novelty
    b_results = []
    for tb in topics_b:
        best_cos = 0.0
        best_a_cp = None
        for cp in classified_pairs:
            if cp["topic_b"]["topic_index"] == tb["topic_index"]:
                if cp["cosine_score"] > best_cos:
                    best_cos = cp["cosine_score"]
                    best_a_cp = cp

        if best_a_cp:
            probs = best_a_cp.get("probabilities") or {}
            p_high = probs.get("highly_similar") or 0.0
            p_part = probs.get("partially_similar") or 0.0
            lbl = best_a_cp["predicted_label"]

            if best_cos >= 0.35 or (best_cos >= 0.22 and lbl == "highly_similar"):
                b_match_status = "matched"
            elif (0.20 <= best_cos < 0.35) or (best_cos >= 0.14 and (p_high + p_part) >= 0.50):
                b_match_status = "partially_matched"
            else:
                b_match_status = "unmatched"
        else:
            b_match_status = "unmatched"

        b_results.append({
            "topic": tb,
            "match_status": b_match_status,
            "best_match": best_a_cp,
        })

    # ── Aggregate counts and percentages ──────────────────────────
    label_counts = {"highly_similar": 0, "partially_similar": 0, "unrelated": 0}
    for cp in classified_pairs:
        lbl = cp["predicted_label"]
        if lbl in label_counts:
            label_counts[lbl] += 1

    a_matched = sum(1 for r in a_results if r["match_status"] == "matched")
    a_partial = sum(1 for r in a_results if r["match_status"] == "partially_matched")
    a_unmatched = sum(1 for r in a_results if r["match_status"] == "unmatched")

    b_matched = sum(1 for r in b_results if r["match_status"] == "matched")
    b_partial = sum(1 for r in b_results if r["match_status"] == "partially_matched")
    b_unmatched = sum(1 for r in b_results if r["match_status"] == "unmatched")

    total_a = len(topics_a) or 1
    pct_matched = round(100.0 * a_matched / total_a, 1)
    pct_partial = round(100.0 * a_partial / total_a, 1)
    pct_unmatched = round(100.0 * a_unmatched / total_a, 1)
    overlap_pct = round(100.0 * (a_matched + 0.5 * a_partial) / total_a, 1)

    return {
        "classified_pairs": classified_pairs,
        "topics_a_results": a_results,
        "topics_b_results": b_results,
        "summary": {
            "total_topics_a": len(topics_a),
            "total_topics_b": len(topics_b),
            "total_candidate_pairs": len(classified_pairs),
            "label_distribution": {
                "highly_similar": a_matched,
                "partially_similar": a_partial,
                "unrelated": a_unmatched,
            },
            "candidate_pair_distribution": label_counts,
            "topics_a_matched": a_matched,
            "topics_a_partial": a_partial,
            "topics_a_unmatched": a_unmatched,
            "topics_b_matched": b_matched,
            "topics_b_partial": b_partial,
            "topics_b_unmatched": b_unmatched,
            "overlap_percentage": overlap_pct,
            "pct_matched": pct_matched,
            "pct_partial": pct_partial,
            "pct_unmatched": pct_unmatched,
        },
    }
