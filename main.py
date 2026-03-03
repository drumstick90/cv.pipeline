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

    # Run pipeline
    try:
        result = run(
            resume=resume_text,
            target_role=args.role,
            job_description=job_description,
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
    if cost:
        print(f"Cost: ${cost:.4f}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
