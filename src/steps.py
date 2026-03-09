"""Step definitions with prompts from the Riyaz Twitter thread."""

import re
from typing import Any, Optional

# Shared guardrails to reduce hallucinations and sycophancy
NO_HALLUCINATION = "Only use facts, numbers, and metrics that appear in the source resume. Do not invent, extrapolate, or fabricate any data."
NO_SYCOPHANCY = "Use professional, direct language. Avoid flattery, superlatives, or excessive praise. Be factual and credible."

# Default prompts as templates. Use {{var}} for substitution.
PROMPTS = {
    "guardrails": {
        "no_hallucination": NO_HALLUCINATION,
        "no_sycophancy": NO_SYCOPHANCY,
    },
    "step_1": {
        "user": "Act as a senior recruiter who screens 300 resumes per week. Identify exactly why my resume may be ignored within 10 seconds. Flag weak positioning, vague impact, and structural issues. Resume: {{resume}}. Target role: {{target_role}}.",
        "system": None,
    },
    "step_2": {
        "user": "Rewrite my professional summary to clearly position me for {{target_role}}. Define who I am, what I specialize in, and what results I consistently deliver. Keep it sharp and specific. {{no_hallucination}} {{no_sycophancy}}\n\n{{audit_section}}\nResume: {{resume}}",
        "system": "Return the complete revised resume with the new professional summary integrated. Do not return only the summary - return the full resume document.",
    },
    "step_3": {
        "user": "Convert every responsibility in my resume into a measurable achievement. Replace task-based statements with result-driven bullet points. Use only metrics and outcomes that are stated or clearly implied in the source resume. {{no_hallucination}} If no numbers exist, describe impact qualitatively without inventing figures. Resume: {{resume}}.",
        "system": "Return the complete revised resume with all responsibilities converted to achievements. Do not invent metrics or numbers. Output the full resume document only.",
    },
    "step_4": {
        "user": "Compare my resume with this job description and identify missing keywords. Rewrite my resume to align naturally with the role without keyword stuffing. {{no_hallucination}} Resume: {{resume}}. Job description: {{job_description}}.",
        "system": "Return the complete revised resume with ATS keywords aligned. Output the full resume document only.",
    },
    "step_5": {
        "user": "Rewrite my resume using concise, confident, professional language. Remove filler words, passive phrases, and generic statements while preserving full accuracy. {{no_sycophancy}} Resume: {{resume}}.",
        "system": "Return the complete revised resume with executive tone. Output the full resume document only.",
    },
    "step_6": {
        "user": "Reformat my resume so the most impressive achievements and skills are visible within the first 10 seconds. Improve structure, visual hierarchy, and clarity throughout. {{no_hallucination}} Resume: {{resume}}.",
        "system": "Return the complete revised resume with the new structure and hierarchy. Output the full resume document only.",
    },
    "step_7": {
        "user": "Review my revised resume and refine it into a clean, high-impact, interview-ready document that communicates value immediately. {{no_hallucination}} {{no_sycophancy}} Resume: {{resume}}.",
        "system": "Return the complete revised resume. Output the full resume document only.",
    },
}


def _render(template: str, vars: dict[str, Any]) -> str:
    """Replace {{key}} with vars[key]. Keys not in vars become empty string."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return str(vars.get(key, ""))
    return re.sub(r"\{\{(\w+)\}\}", repl, template)


def build_prompt(step_id: str, prompts: dict, vars: dict[str, Any]) -> tuple[str, Optional[str]]:
    """
    Build user and system prompts for a step.
    prompts: dict from PROMPTS or custom overrides.
    vars: resume, target_role, audit_section, job_description, no_hallucination, no_sycophancy.
    Returns (user_prompt, system_prompt).
    """
    step_key = f"step_{step_id}" if isinstance(step_id, int) else step_id
    step_data = prompts.get(step_key, PROMPTS.get(step_key, {}))
    guardrails = prompts.get("guardrails", PROMPTS.get("guardrails", {}))
    merged = {
        **vars,
        "no_hallucination": guardrails.get("no_hallucination", NO_HALLUCINATION),
        "no_sycophancy": guardrails.get("no_sycophancy", NO_SYCOPHANCY),
    }
    user_tpl = step_data.get("user", "")
    system_tpl = step_data.get("system")
    user = _render(user_tpl, merged) if user_tpl else ""
    system = _render(system_tpl, merged) if system_tpl else None
    return user, system


def step_1_brutal_audit(resume: str, target_role: str, prompts: Optional[dict] = None) -> str:
    """Brutal Recruiter Audit."""
    p = prompts or PROMPTS
    user, _ = build_prompt(1, p, {"resume": resume, "target_role": target_role, "audit_section": ""})
    return user


def step_2_positioning_reset(
    resume: str,
    target_role: str,
    audit: Optional[str] = None,
    prompts: Optional[dict] = None,
) -> str:
    """Positioning and Personal Brand Reset."""
    p = prompts or PROMPTS
    audit_section = ""
    if audit:
        audit_section = f"First, here is a recruiter audit of my current resume that identified these issues:\n{audit}\n\nAddress these issues in your rewrite.\n\n"
    user, _ = build_prompt(2, p, {"resume": resume, "target_role": target_role, "audit_section": audit_section})
    return user


def step_3_achievement_conversion(resume: str, prompts: Optional[dict] = None) -> str:
    """Achievement Conversion."""
    p = prompts or PROMPTS
    user, _ = build_prompt(3, p, {"resume": resume, "audit_section": ""})
    return user


def step_4_ats_alignment(resume: str, job_description: str, prompts: Optional[dict] = None) -> str:
    """ATS Keyword Alignment."""
    p = prompts or PROMPTS
    user, _ = build_prompt(4, p, {"resume": resume, "job_description": job_description, "audit_section": ""})
    return user


def step_5_executive_tone(resume: str, prompts: Optional[dict] = None) -> str:
    """Executive Tone Upgrade."""
    p = prompts or PROMPTS
    user, _ = build_prompt(5, p, {"resume": resume, "audit_section": ""})
    return user


def step_6_scan_optimization(resume: str, prompts: Optional[dict] = None) -> str:
    """10-Second Scan Optimization."""
    p = prompts or PROMPTS
    user, _ = build_prompt(6, p, {"resume": resume, "audit_section": ""})
    return user


def step_7_final_polish(resume: str, prompts: Optional[dict] = None) -> str:
    """Final Executive Polish."""
    p = prompts or PROMPTS
    user, _ = build_prompt(7, p, {"resume": resume, "audit_section": ""})
    return user


def get_system_prompt(step_id: int, prompts: Optional[dict] = None) -> Optional[str]:
    """Get system prompt for step (2-7)."""
    p = prompts or PROMPTS
    _, system = build_prompt(step_id, p, {"resume": "", "audit_section": ""})
    return system
