"""
app.py  –  CurriculumLens Flask Application
"""

import json
import os
import sys
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
import io

# Project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.topic_extractor import extract_text, extract_topics
from src.single_analysis import analyze_single_syllabus
from src.comparison_analysis import analyze_comparison
from src.syllabus_classifier import is_model_available, get_metadata
from src.report_generator import (
    generate_comparison_csv,
    generate_comparison_pdf,
    generate_single_csv,
    generate_single_pdf,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB limit
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "curriculum-lens-dev-key")

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}
EVALUATION_DIR = Path(__file__).resolve().parent / "evaluation"
MODELS_DIR = Path(__file__).resolve().parent / "models"


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _read_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# ── Page Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", model_available=is_model_available())


@app.route("/analyze-single")
def single_page():
    return render_template("single_analysis.html")


@app.route("/compare")
def compare_page():
    return render_template("comparison.html")


@app.route("/model-performance")
def model_performance_page():
    metrics = _read_json(EVALUATION_DIR / "metrics.json")
    val_comparison = _read_json(EVALUATION_DIR / "validation_comparison.json")
    metadata = get_metadata()
    return render_template(
        "model_performance.html",
        metrics=metrics,
        val_comparison=val_comparison,
        metadata=metadata,
        model_available=is_model_available(),
    )


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_available": is_model_available(),
        "model_metadata": get_metadata() if is_model_available() else None,
    })


@app.route("/api/analyze-single", methods=["POST"])
def api_analyze_single():
    if "syllabus" not in request.files:
        return jsonify({"error": "No file uploaded. Please upload a syllabus file."}), 400

    file = request.files["syllabus"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    try:
        file_bytes = file.read()
        text = extract_text(file.filename, file_bytes)
        topics = extract_topics(text, doc_name=file.filename)

        if not topics:
            return jsonify({"error": "No topics could be extracted. Check document formatting."}), 422

        result = analyze_single_syllabus(topics, doc_name=file.filename)
        result["extracted_text_preview"] = text[:1500]
        return jsonify({"success": True, "result": result})

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred during analysis."}), 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    if not is_model_available():
        return jsonify({
            "error": "Trained model not found. Please run: python train_model.py"
        }), 503

    for key in ("syllabus_a", "syllabus_b"):
        if key not in request.files:
            return jsonify({"error": f"Missing file: {key}"}), 400

    file_a = request.files["syllabus_a"]
    file_b = request.files["syllabus_b"]

    for f in (file_a, file_b):
        if not f.filename:
            return jsonify({"error": "Empty filename for one of the uploads."}), 400
        if not allowed_file(f.filename):
            return jsonify({"error": f"Unsupported file type: {f.filename}"}), 400

    try:
        bytes_a = file_a.read()
        bytes_b = file_b.read()

        text_a = extract_text(file_a.filename, bytes_a)
        text_b = extract_text(file_b.filename, bytes_b)

        topics_a = extract_topics(text_a, doc_name=file_a.filename)
        topics_b = extract_topics(text_b, doc_name=file_b.filename)

        result = analyze_comparison(topics_a, topics_b, file_a.filename, file_b.filename)

        if "error" in result:
            return jsonify({"error": result["error"]}), 422

        return jsonify({"success": True, "result": result})

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred during comparison."}), 500


@app.route("/api/model-performance")
def api_model_performance():
    metrics = _read_json(EVALUATION_DIR / "metrics.json")
    val_comparison = _read_json(EVALUATION_DIR / "validation_comparison.json")
    metadata = get_metadata()
    if not metrics:
        return jsonify({
            "available": False,
            "message": "Model has not been evaluated yet. Run: python evaluate_model.py",
        })
    return jsonify({
        "available": True,
        "test_metrics": metrics,
        "validation_comparison": val_comparison,
        "metadata": metadata,
    })


@app.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    try:
        data = request.get_json(force=True)
        mode = data.get("mode", "comparison")
        result = data.get("result", {})

        if mode == "comparison":
            csv_bytes = generate_comparison_csv(result)
            filename = "curriculum_comparison.csv"
        else:
            csv_bytes = generate_single_csv(result)
            filename = "syllabus_analysis.csv"

        return send_file(
            io.BytesIO(csv_bytes),
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to generate CSV report."}), 500


@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    try:
        data = request.get_json(force=True)
        mode = data.get("mode", "comparison")
        result = data.get("result", {})

        if mode == "comparison":
            pdf_bytes = generate_comparison_pdf(result)
            filename = "curriculum_comparison.pdf"
        else:
            pdf_bytes = generate_single_pdf(result)
            filename = "syllabus_analysis.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to generate PDF report."}), 500


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum upload size is 20 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return render_template("index.html", model_available=is_model_available()), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"\n  CurriculumLens starting on http://localhost:{port}")
    if not is_model_available():
        print("  ⚠  Trained model not found — run: python train_model.py")
    app.run(host="0.0.0.0", port=port, debug=debug)
