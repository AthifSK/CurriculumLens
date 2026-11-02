"""
report_generator.py
Generates CSV and PDF reports from analysis results.
"""

import io
import csv
from datetime import datetime


def generate_comparison_csv(comparison_result: dict) -> bytes:
    """Generate a CSV report from two-syllabus comparison results."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "topic_a", "unit_a", "topic_b", "unit_b",
        "predicted_label", "confidence", "cosine_score", "match_status"
    ])

    matching = comparison_result.get("matching", {})
    for r in matching.get("topics_a_results", []):
        ta = r["topic"]
        best = r.get("best_match")
        if best:
            tb = best["topic_b"]
            writer.writerow([
                ta["topic_name"],
                ta["unit_name"],
                tb["topic_name"],
                tb["unit_name"],
                best["predicted_label"],
                best.get("confidence", ""),
                best.get("cosine_score", ""),
                r["match_status"],
            ])
        else:
            writer.writerow([
                ta["topic_name"],
                ta["unit_name"],
                "—", "—",
                "unrelated", "", "",
                "unmatched",
            ])

    return output.getvalue().encode("utf-8")


def generate_single_csv(analysis_result: dict) -> bytes:
    """Generate a CSV report from single-syllabus analysis."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "topic_index", "unit_name", "topic_name",
        "best_related_topic", "best_related_unit", "relation_level", "is_cross_unit"
    ])
    for t in analysis_result.get("topics", []):
        writer.writerow([
            t.get("topic_index", ""),
            t.get("unit_name", ""),
            t.get("topic_name", ""),
            t.get("best_related_topic", t.get("cluster", "")),
            t.get("best_related_unit", ""),
            t.get("relation_level", ""),
            t.get("is_cross_unit", ""),
        ])
    return output.getvalue().encode("utf-8")


def generate_comparison_pdf(comparison_result: dict) -> bytes:
    """Generate a PDF report using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    heading1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=8)
    heading2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=10)

    story = []

    # Title
    story.append(Paragraph("CurriculumLens – Syllabus Comparison Report", heading1))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3B82F6")))
    story.append(Spacer(1, 0.4*cm))

    # Document names
    name_a = comparison_result.get("name_a", "Syllabus A")
    name_b = comparison_result.get("name_b", "Syllabus B")
    story.append(Paragraph(f"<b>Existing Syllabus:</b> {name_a}", normal))
    story.append(Paragraph(f"<b>Proposed Syllabus:</b> {name_b}", normal))
    story.append(Spacer(1, 0.4*cm))

    # Summary
    matching = comparison_result.get("matching", {})
    summary = matching.get("summary", {})
    if summary:
        story.append(Paragraph("Summary", heading2))
        summary_data = [
            ["Metric", "Value"],
            ["Total Topics – Existing Syllabus", str(summary.get("total_topics_a", "—"))],
            ["Total Topics – Proposed Syllabus", str(summary.get("total_topics_b", "—"))],
            ["Topics Matched (Existing)", str(summary.get("topics_a_matched", "—"))],
            ["Topics Partially Matched (Existing)", str(summary.get("topics_a_partial", "—"))],
            ["Topics Unmatched (Existing)", str(summary.get("topics_a_unmatched", "—"))],
            ["Potentially New Topics (Proposed)", str(summary.get("topics_b_unmatched", "—"))],
            ["Matches %", f"{summary.get('pct_matched', '—')}%"],
            ["Partial Overlap %", f"{summary.get('pct_partial', '—')}%"],
            ["Mismatches %", f"{summary.get('pct_unmatched', '—')}%"],
            ["Total Curriculum Overlap %", f"{summary.get('overlap_percentage', '—')}%"],
        ]
        t_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ])
        tbl = Table(summary_data, colWidths=[10*cm, 5*cm])
        tbl.setStyle(t_style)
        story.append(tbl)
        story.append(Spacer(1, 0.5*cm))

    # Topic matching table
    story.append(Paragraph("Topic Matching Results", heading2))
    rows = [["Topic A", "Unit A", "Topic B", "Unit B", "Label", "Conf."]]
    for r in matching.get("topics_a_results", [])[:40]:
        ta = r["topic"]
        best = r.get("best_match")
        if best:
            tb = best["topic_b"]
            lbl = best.get("predicted_label", "")
            conf = f"{best.get('confidence', ''):.2f}" if best.get("confidence") else "—"
        else:
            tb = {"topic_name": "—", "unit_name": "—"}
            lbl = "unrelated"
            conf = "—"

        rows.append([
            Paragraph(ta["topic_name"][:60], small),
            Paragraph(ta["unit_name"][:30], small),
            Paragraph(tb["topic_name"][:60], small),
            Paragraph(tb["unit_name"][:30], small),
            Paragraph(lbl, small),
            Paragraph(conf, small),
        ])

    tbl2 = Table(rows, colWidths=[4*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm, 1.5*cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tbl2)
    story.append(Spacer(1, 0.5*cm))

    # Limitations
    story.append(Paragraph("Limitations & Interpretation Notes", heading2))
    limitations = [
        "All primary training examples are synthetic. Results on real syllabi may differ.",
        "TF-IDF cannot capture semantic equivalence across different terminology.",
        "Topic extraction quality depends on syllabus formatting.",
        "Model confidence values are class probabilities, not literal overlap percentages.",
        "Topics labelled 'potentially new' are new relative to the existing syllabus only.",
        "Human review of borderline cases is strongly recommended.",
    ]
    for note in limitations:
        story.append(Paragraph(f"• {note}", normal))

    doc.build(story)
    return buffer.getvalue()


def generate_single_pdf(analysis_result: dict) -> bytes:
    """Generate a PDF report for single-syllabus analysis."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    heading1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=8)
    heading2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=10)

    story = []

    story.append(Paragraph("CurriculumLens – Single Syllabus Analysis Report", heading1))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal))
    story.append(Paragraph(f"<b>Document:</b> {analysis_result.get('doc_name', 'Unknown')}", normal))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3B82F6")))
    story.append(Spacer(1, 0.4*cm))

    # Summary
    story.append(Paragraph("Summary & Structure Metrics", heading2))
    summary_data = [
        ["Metric", "Value"],
        ["Total Topics", str(analysis_result.get("total_topics", "—"))],
        ["Total Units", str(analysis_result.get("total_units", "—"))],
        ["Avg Topics/Unit", str(analysis_result.get("avg_topics_per_unit", "—"))],
        ["Curriculum Coherence %", f"{analysis_result.get('coherence_percentage', '—')}%"],
        ["Interconnected Topics %", f"{analysis_result.get('pct_connected', '—')}%"],
        ["Cross-Unit Integration %", f"{analysis_result.get('pct_cross_unit', '—')}%"],
        ["Distinct / Focused Topics %", f"{analysis_result.get('pct_standalone', '—')}%"],
    ]
    tbl = Table(summary_data, colWidths=[10*cm, 5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))

    # Topic inventory
    story.append(Paragraph("Extracted Topics & Internal Linkages", heading2))
    rows = [["#", "Unit", "Topic", "Related Concept", "Level", "Cross-Unit?"]]
    for t in analysis_result.get("topics", [])[:60]:
        rows.append([
            str(t.get("topic_index", "")),
            Paragraph(t.get("unit_name", "")[:30], small),
            Paragraph(t.get("topic_name", "")[:50], small),
            Paragraph(t.get("best_related_topic", "—")[:50], small),
            Paragraph(str(t.get("relation_level", "")).capitalize(), small),
            Paragraph("Yes" if t.get("is_cross_unit") else "No", small),
        ])
    tbl2 = Table(rows, colWidths=[0.8*cm, 3.2*cm, 5.5*cm, 5.0*cm, 1.8*cm, 1.7*cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tbl2)

    doc.build(story)
    return buffer.getvalue()
