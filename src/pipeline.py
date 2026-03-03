"""Pipeline orchestrator - runs resume improvement steps in sequence."""

import sys
from typing import Optional

from .claude import complete
from . import steps


def run(
    resume: str,
    target_role: str,
    job_description: Optional[str] = None,
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
    """
    result: dict = {
        "audit": "",
        "final_resume": "",
        "steps": [],
        "cost_usd": 0.0,
    }
    total_cost = 0.0

    # Step 1: Brutal Recruiter Audit
    print("Step 1/7: Brutal Recruiter Audit...", file=sys.stderr)
    audit, cost = complete(steps.step_1_brutal_audit(resume, target_role))
    total_cost += cost
    result["audit"] = audit
    result["steps"].append({"step": 1, "name": "audit", "output": audit})

    # Step 2: Positioning and Personal Brand Reset (uses audit from step 1)
    print("Step 2/7: Positioning and Personal Brand Reset...", file=sys.stderr)
    resume_v2, cost = complete(
        steps.step_2_positioning_reset(resume, target_role, audit),
        system=steps.STEP_2_SYSTEM,
    )
    total_cost += cost
    result["steps"].append({"step": 2, "name": "resume", "output": resume_v2})

    current_resume = resume_v2

    # Step 3: Achievement Conversion
    print("Step 3/7: Achievement Conversion...", file=sys.stderr)
    resume_v3, cost = complete(
        steps.step_3_achievement_conversion(current_resume),
        system=steps.STEP_3_SYSTEM,
    )
    total_cost += cost
    result["steps"].append({"step": 3, "name": "resume", "output": resume_v3})

    current_resume = resume_v3

    # Step 4: ATS Keyword Alignment (skip if no job description)
    if job_description:
        print("Step 4/7: ATS Keyword Alignment...", file=sys.stderr)
        resume_v4, cost = complete(
            steps.step_4_ats_alignment(current_resume, job_description),
            system=steps.STEP_4_SYSTEM,
        )
        total_cost += cost
        result["steps"].append({"step": 4, "name": "resume", "output": resume_v4})
        current_resume = resume_v4
    else:
        print(
            "Step 4/7: ATS Keyword Alignment (skipped - no job description)...",
            file=sys.stderr,
        )

    # Step 5: Executive Tone Upgrade
    print("Step 5/7: Executive Tone Upgrade...", file=sys.stderr)
    resume_v5, cost = complete(
        steps.step_5_executive_tone(current_resume),
        system=steps.STEP_5_SYSTEM,
    )
    total_cost += cost
    result["steps"].append({"step": 5, "name": "resume", "output": resume_v5})

    current_resume = resume_v5

    # Step 6: 10-Second Scan Optimization
    print("Step 6/7: 10-Second Scan Optimization...", file=sys.stderr)
    resume_v6, cost = complete(
        steps.step_6_scan_optimization(current_resume),
        system=steps.STEP_6_SYSTEM,
    )
    total_cost += cost
    result["steps"].append({"step": 6, "name": "resume", "output": resume_v6})

    current_resume = resume_v6

    # Step 7: Final Executive Polish
    print("Step 7/7: Final Executive Polish...", file=sys.stderr)
    final_resume, cost = complete(
        steps.step_7_final_polish(current_resume),
        system=steps.STEP_7_SYSTEM,
    )
    total_cost += cost
    result["final_resume"] = final_resume
    result["steps"].append({"step": 7, "name": "resume", "output": final_resume})
    result["cost_usd"] = round(total_cost, 6)

    return result
