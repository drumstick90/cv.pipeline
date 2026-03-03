#!/usr/bin/env python3
"""CLI for the CV pipeline - stepped resume improvement via Claude API."""

import argparse
import os
import sys
from pathlib import Path

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.pipeline import run


def _fmt_tokens(n: int) -> str:
    if n >= 1000:
        return f"~{n / 1000:.1f}k"
    return f"~{n}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 7-step resume improvement pipeline via Claude API."
    )
    parser.add_argument(
        "resume",
        type=Path,
        help="Path to resume file (plain text; paste text from PDF to avoid token waste)",
    )
    parser.add_argument(
        "--role",
        "-r",
        required=True,
        help="Target role (e.g. 'Senior Software Engineer')",
    )
    parser.add_argument(
        "--job-description",
        "-j",
        type=Path,
        default=None,
        help="Path to job description file (optional, for ATS alignment in step 4)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("./output"),
        help="Directory for final resume only (default: ./output)",
    )
    parser.add_argument(
        "--log-dir",
        "-l",
        type=Path,
        default=Path("./log"),
        help="Directory for complete step logs (default: ./log)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Extra verbose logs (API send/wait messages)",
    )

    args = parser.parse_args()

    # Read resume
    if not args.resume.exists():
        print(f"Error: Resume file not found: {args.resume}", file=sys.stderr)
        return 1

    resume_text = args.resume.read_text(encoding="utf-8")

    # Read job description if provided
    job_description = None
    if args.job_description:
        if not args.job_description.exists():
            print(
                f"Error: Job description file not found: {args.job_description}",
                file=sys.stderr,
            )
            return 1
        job_description = args.job_description.read_text(encoding="utf-8")

    def on_progress(step_num: int, step_name: str, phase: str, elapsed_s: float, usage: dict):
        if phase == "start":
            print(f"→ Step {step_num}/7: {step_name}... (calling Claude)", file=sys.stderr)
            if args.verbose:
                print("  Sending request...", file=sys.stderr)
        elif phase == "skipped":
            print(f"○ Step {step_num}/7: {step_name} (skipped)", file=sys.stderr)
        elif phase == "end":
            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            total = inp + out
            cost = usage.get("cost_usd", 0)
            print(
                f"✓ Step {step_num} done in {elapsed_s:.1f}s ({_fmt_tokens(total)} tokens, ${cost:.4f})",
                file=sys.stderr,
            )
            if args.verbose:
                print("  Parsing response...", file=sys.stderr)

    # Run pipeline
    try:
        result = run(
            resume=resume_text,
            target_role=args.role,
            job_description=job_description,
            on_progress=on_progress,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create directories
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    # Save complete logs to log dir
    for s in result["steps"]:
        step_num = s["step"]
        name = s["name"]
        output = s["output"]
        log_path = args.log_dir / f"step_{step_num}_{name}.txt"
        log_path.write_text(output, encoding="utf-8")
        print(f"Step {step_num} logged to {log_path}", file=sys.stderr)

    # Save final resume to output dir only
    final_path = args.output_dir / "resume_final.txt"
    final_path.write_text(result["final_resume"], encoding="utf-8")
    print(f"Final resume saved to {final_path}", file=sys.stderr)

    cost = result.get("cost_usd", 0)
    elapsed = result.get("total_elapsed_s", 0)
    inp = result.get("total_input_tokens", 0)
    out = result.get("total_output_tokens", 0)
    print(file=sys.stderr)
    print(
        f"Done in {elapsed:.1f}s | {_fmt_tokens(inp + out)} tokens | ${cost:.4f}",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
