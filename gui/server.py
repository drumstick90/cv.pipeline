#!/usr/bin/env python3
"""Minimal 00s-style web GUI for CV pipeline."""

import os
import re
import sys
import threading
import uuid
from pathlib import Path

# Ensure project root is on path when run from gui/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, send_from_directory

from src.pdf_extract import extract_text_from_pdf

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.pipeline import run, PipelineAborted

app = Flask(__name__, static_folder="static")
jobs: dict = {}
jobs_lock = threading.Lock()
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "x-api-key",
    "anthropic_api_key",
}
_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9\-_]+"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-]+)"),
]


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]" if pattern.groups >= 1 else "[REDACTED]", redacted)
    return redacted


def _redact_sensitive(value):
    if isinstance(value, dict):
        redacted: dict = {}
        for key, item in value.items():
            key_name = key.lower() if isinstance(key, str) else str(key).lower()
            if key_name in _SENSITIVE_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_sensitive(item) for item in value)
    if isinstance(value, str):
        return _redact_text(value)
    return value

@app.route("/api/check-key")
def api_check_key():
    """Return whether ANTHROPIC_API_KEY is set (for showing API key input when empty)."""
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    return jsonify({"has_key": has_key})


@app.route("/api/prompts")
def api_prompts():
    """Return default prompts for editing. Structure: guardrails, step_1..step_7."""
    from src.steps import PROMPTS
    return jsonify(PROMPTS)


@app.route("/api/model")
def api_model():
    """Return the model that will be used for pipeline runs."""
    try:
        from src.claude import get_available_model
        model = get_available_model(prefer="sonnet")
        return jsonify({"model": model})
    except Exception as e:
        return jsonify({"model": None, "error": str(e)}), 500


@app.route("/api/extract-pdf", methods=["POST"])
def api_extract_pdf():
    """
    Extract text from uploaded PDF (simulates CMD+A -> CMD+C).
    No AI parsing — raw text extraction only.
    """
    if "file" not in request.files and "pdf" not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400
    file = request.files.get("file") or request.files.get("pdf")
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400
    try:
        pdf_bytes = file.read()
        text = extract_text_from_pdf(pdf_bytes)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"Failed to extract text: {e}"}), 500


def _fmt_tokens(n: int) -> str:
    if n >= 1000:
        return f"~{n / 1000:.1f}k"
    return f"~{n}"


def run_pipeline(
    job_id: str,
    resume: str,
    target_role: str,
    job_description: str | None,
    api_key: str | None = None,
    prompts: dict | None = None,
):
    def _log(prog: dict, line: str):
        prog.setdefault("log", []).append(_redact_text(line))

    def on_progress(step_num: int, step_name: str, phase: str, elapsed_s: float, usage: dict):
        with jobs_lock:
            job = jobs.get(job_id)
            if not job or job.get("status") != "running":
                return
            prog = job.setdefault("progress", {})
            if phase == "start":
                prog["current_step"] = step_num
                prog["step_name"] = step_name
                prog["elapsed_ms"] = 0
                _log(prog, f"→ Step {step_num}/7: {step_name}... (calling Claude)")
                _log(prog, "  Sending request...")
            elif phase == "skipped":
                prog.setdefault("completed_steps", []).append(step_num)
                _log(prog, f"○ Step {step_num}/7: {step_name} (skipped)")
            elif phase == "end":
                prog.setdefault("completed_steps", []).append(step_num)
                prog["current_step"] = step_num
                prog["step_name"] = step_name
                prog["elapsed_ms"] = int(elapsed_s * 1000)
                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cost = usage.get("cost_usd", 0)
                _log(prog, f"✓ Step {step_num} done in {elapsed_s:.1f}s ({_fmt_tokens(inp + out)} tokens, ${cost:.4f})")
                _log(prog, "  Parsing response...")
                payload = usage.get("payload")
                if payload is not None:
                    prog.setdefault("step_payloads", {})[step_num] = _redact_sensitive(payload)

    def abort_check():
        with jobs_lock:
            return jobs.get(job_id, {}).get("status") != "running"

    try:
        result = run(
            resume=resume,
            target_role=target_role,
            job_description=job_description,
            api_key=api_key,
            prompts=prompts,
            on_progress=on_progress,
            abort_check=abort_check,
        )
        with jobs_lock:
            job = jobs.get(job_id)
            prog = job.get("progress") or {}
            log_lines = list(prog.get("log", []))
            elapsed = result.get("total_elapsed_s", 0)
            inp = result.get("total_input_tokens", 0)
            out = result.get("total_output_tokens", 0)
            total_tok = inp + out
            tok_str = _fmt_tokens(total_tok) if total_tok else "0"
            cost = result.get("cost_usd", 0)
            log_lines.append(f"Done in {elapsed:.1f}s | {tok_str} tokens | ${cost:.4f}")
            jobs[job_id] = {
                "status": "done",
                "result": result,
                "log_lines": _redact_sensitive(log_lines[-2:]),
                "step_payloads": _redact_sensitive(prog.get("step_payloads", {})),
            }
    except PipelineAborted:
        with jobs_lock:
            job = jobs.get(job_id)
            prog = (job or {}).get("progress", {})
            log_lines = list(prog.get("log", []))
            log_lines.append("Aborted by user.")
            jobs[job_id] = {"status": "aborted", "log_lines": _redact_sensitive(log_lines)}
    except Exception as e:
        with jobs_lock:
            jobs[job_id] = {"status": "error", "error": _redact_text(str(e))}


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
    data.pop("api_key", None)
    prompts = data.get("prompts")  # optional; if provided, use custom prompts

    if not resume or not target_role:
        return jsonify({"error": "Resume and target role are required"}), 400

    if not os.environ.get("ANTHROPIC_API_KEY", "").strip() and not api_key:
        return jsonify({"error": "API key required. Set ANTHROPIC_API_KEY in .env or enter it above."}), 400

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "running", "progress": {"current_step": 0, "step_name": "", "completed_steps": []}}

    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, resume, target_role, job_description, api_key, prompts),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/abort/<job_id>", methods=["POST"])
def api_abort(job_id):
    """Request abort of a running job. Takes effect at the next step boundary."""
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] != "running":
        return jsonify({"ok": True, "message": "Job already finished"})
    with jobs_lock:
        jobs[job_id]["status"] = "aborting"
    return jsonify({"ok": True})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] == "aborting":
        return jsonify({"status": "running", "aborting": True})
    if job["status"] == "done":
        return jsonify({
            "status": "done",
            "final_resume": job["result"]["final_resume"],
            "audit": job["result"]["audit"],
            "cost_usd": job["result"].get("cost_usd", 0),
            "log_lines": _redact_sensitive(job.get("log_lines", [])),
            "step_payloads": _redact_sensitive(job.get("step_payloads", {})),
        })
    if job["status"] == "error":
        return jsonify({"status": "error", "error": _redact_text(job["error"])}), 500
    if job["status"] == "aborted":
        return jsonify({
            "status": "aborted",
            "log_lines": _redact_sensitive(job.get("log_lines", [])),
        })
    prog = job.get("progress", {})
    log_lines = prog.get("log", [])
    return jsonify({
        "status": "running",
        "current_step": prog.get("current_step", 0),
        "step_name": prog.get("step_name", ""),
        "elapsed_ms": prog.get("elapsed_ms", 0),
        "completed_steps": prog.get("completed_steps", []),
        "log_lines": _redact_sensitive(log_lines[-2:]),  # last 2 lines for display
        "step_payloads": _redact_sensitive(prog.get("step_payloads", {})),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
