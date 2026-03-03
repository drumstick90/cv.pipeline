#!/usr/bin/env python3
"""Minimal 00s-style web GUI for CV pipeline."""

import os
import sys
import threading
import uuid
from pathlib import Path

# Ensure project root is on path when run from gui/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, send_from_directory

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.pipeline import run

app = Flask(__name__, static_folder="static")
jobs: dict = {}
jobs_lock = threading.Lock()


@app.route("/api/check-key")
def api_check_key():
    """Return whether ANTHROPIC_API_KEY is set (for showing API key input when empty)."""
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    return jsonify({"has_key": has_key})


def run_pipeline(
    job_id: str,
    resume: str,
    target_role: str,
    job_description: str | None,
    api_key: str | None = None,
):
    try:
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        result = run(resume=resume, target_role=target_role, job_description=job_description)
        with jobs_lock:
            jobs[job_id] = {"status": "done", "result": result}
    except Exception as e:
        with jobs_lock:
            jobs[job_id] = {"status": "error", "error": str(e)}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json() or {}
    # #region agent log
    def _safe(v):
        return (v or "").strip() if v is not None else ""
    resume = _safe(data.get("resume")) or data.get("resume", "")
    if resume == data.get("resume", ""):
        resume = (data.get("resume") or "").strip()
    # #endregion
    resume = (data.get("resume") or "").strip()
    target_role = (data.get("target_role") or "").strip()
    job_description = (data.get("job_description") or "").strip() or None
    api_key = (data.get("api_key") or "").strip() or None

    if not resume or not target_role:
        return jsonify({"error": "Resume and target role are required"}), 400

    if not os.environ.get("ANTHROPIC_API_KEY", "").strip() and not api_key:
        return jsonify({"error": "API key required. Set ANTHROPIC_API_KEY in .env or enter it above."}), 400

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "running"}

    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, resume, target_role, job_description, api_key),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] == "done":
        return jsonify({
            "status": "done",
            "final_resume": job["result"]["final_resume"],
            "audit": job["result"]["audit"],
            "cost_usd": job["result"].get("cost_usd", 0),
        })
    if job["status"] == "error":
        return jsonify({"status": "error", "error": job["error"]}), 500
    return jsonify({"status": "running"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
