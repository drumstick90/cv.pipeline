"""Pipeline orchestrator - runs resume improvement steps in sequence."""

import sys
import time
from typing import Callable, Optional

from .claude import complete
from . import steps


class PipelineAborted(Exception):
    """Raised when the pipeline is aborted by the user."""


# Step metadata for progress reporting
STEP_NAMES = {
    1: "Brutal Recruiter Audit",
    2: "Positioning and Personal Brand Reset",
    3: "Achievement Conversion",
    4: "ATS Keyword Alignment",
    5: "Executive Tone Upgrade",
    6: "10-Second Scan Optimization",
    7: "Final Executive Polish",
}


def run(
    resume: str,
    target_role: str,
    job_description: Optional[str] = None,
    prompts: Optional[dict] = None,
    on_progress: Optional[Callable[[int, str, str, float, dict], None]] = None,
    abort_check: Optional[Callable[[], bool]] = None,
) -> dict:
    """
    Run the 7-step resume improvement pipeline.
    Each step's output is fed into the subsequent step.

    Args:
        resume: The resume text.
        target_role: Target job role.
        job_description: Optional job description for ATS alignment (step 4).

    Returns:
        Dict with keys: audit, final_resume, steps (list of step outputs for logging).

    on_progress: Optional callback(step_num, step_name, phase, elapsed_s, usage).
        phase is "start" or "end". usage has input_tokens, output_tokens (0 at start).
    abort_check: Optional callable returning True to abort. Checked before each step.
    """
    result: dict = {
        "audit": "",
        "final_resume": "",
        "steps": [],
        "cost_usd": 0.0,
    }
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    pipeline_start = time.perf_counter()

    def _step(step_num: int, step_name: str, do_run: Callable):
        if abort_check and abort_check():
            raise PipelineAborted()
        nonlocal total_cost, total_input_tokens, total_output_tokens
        start = time.perf_counter()
        if on_progress:
            on_progress(step_num, step_name, "start", 0.0, {"input_tokens": 0, "output_tokens": 0})
        text, cost, usage, payload = do_run()
        elapsed = time.perf_counter() - start
        total_cost += cost
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)
        if on_progress:
            usage_with_cost = {**usage, "cost_usd": cost, "payload": payload}
            on_progress(step_num, step_name, "end", elapsed, usage_with_cost)
        return text

    # Step 1: Brutal Recruiter Audit
    audit = _step(1, STEP_NAMES[1], lambda: complete(steps.step_1_brutal_audit(resume, target_role, prompts)))
    result["audit"] = audit
    result["steps"].append({"step": 1, "name": "audit", "output": audit})

    # Step 2: Positioning and Personal Brand Reset (uses audit from step 1)
    resume_v2 = _step(
        2,
        STEP_NAMES[2],
        lambda: complete(
            steps.step_2_positioning_reset(resume, target_role, audit, prompts),
            system=steps.get_system_prompt(2, prompts),
        ),
    )
    result["steps"].append({"step": 2, "name": "resume", "output": resume_v2})
    current_resume = resume_v2

    # Step 3: Achievement Conversion
    resume_v3 = _step(
        3,
        STEP_NAMES[3],
        lambda: complete(
            steps.step_3_achievement_conversion(current_resume, prompts),
            system=steps.get_system_prompt(3, prompts),
        ),
    )
    result["steps"].append({"step": 3, "name": "resume", "output": resume_v3})
    current_resume = resume_v3

    # Step 4: ATS Keyword Alignment (skip if no job description)
    if abort_check and abort_check():
        raise PipelineAborted()
    if job_description:
        resume_v4 = _step(
            4,
            STEP_NAMES[4],
            lambda: complete(
                steps.step_4_ats_alignment(current_resume, job_description, prompts),
                system=steps.get_system_prompt(4, prompts),
            ),
        )
        result["steps"].append({"step": 4, "name": "resume", "output": resume_v4})
        current_resume = resume_v4
    else:
        if on_progress:
            on_progress(4, STEP_NAMES[4], "skipped", 0.0, {"input_tokens": 0, "output_tokens": 0})

    # Step 5: Executive Tone Upgrade
    resume_v5 = _step(
        5,
        STEP_NAMES[5],
        lambda: complete(
            steps.step_5_executive_tone(current_resume, prompts),
            system=steps.get_system_prompt(5, prompts),
        ),
    )
    result["steps"].append({"step": 5, "name": "resume", "output": resume_v5})
    current_resume = resume_v5

    # Step 6: 10-Second Scan Optimization
    resume_v6 = _step(
        6,
        STEP_NAMES[6],
        lambda: complete(
            steps.step_6_scan_optimization(current_resume, prompts),
            system=steps.get_system_prompt(6, prompts),
        ),
    )
    result["steps"].append({"step": 6, "name": "resume", "output": resume_v6})
    current_resume = resume_v6

    # Step 7: Final Executive Polish
    final_resume = _step(
        7,
        STEP_NAMES[7],
        lambda: complete(
            steps.step_7_final_polish(current_resume, prompts),
            system=steps.get_system_prompt(7, prompts),
        ),
    )
    result["final_resume"] = final_resume
    result["steps"].append({"step": 7, "name": "resume", "output": final_resume})
    result["cost_usd"] = round(total_cost, 6)
    result["total_elapsed_s"] = round(time.perf_counter() - pipeline_start, 2)
    result["total_input_tokens"] = total_input_tokens
    result["total_output_tokens"] = total_output_tokens

    return result
