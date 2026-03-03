"""Step definitions with prompts from the Riyaz Twitter thread."""

from typing import Optional


def step_1_brutal_audit(resume: str, target_role: str) -> str:
    """Brutal Recruiter Audit - identifies why resume may be ignored."""
    return f'''Act as a senior recruiter who screens 300 resumes per week. Identify exactly why my resume may be ignored within 10 seconds. Flag weak positioning, vague impact, and structural issues. Resume: {resume}. Target role: {target_role}.'''


def step_2_positioning_reset(
    resume: str,
    target_role: str,
    audit: Optional[str] = None,
) -> str:
    """Positioning and Personal Brand Reset - rewrites professional summary."""
    base = f'''Rewrite my professional summary to clearly position me for {target_role}. Define who I am, what I specialize in, and what results I consistently deliver. Keep it sharp, specific, and measurable.'''
    if audit:
        return f'''{base}

First, here is a recruiter audit of my current resume that identified these issues:
{audit}

Address these issues in your rewrite. Resume: {resume}'''
    return f'''{base} Resume: {resume}'''


def step_3_achievement_conversion(resume: str) -> str:
    """Achievement Conversion - converts responsibilities to measurable achievements."""
    return f'''Convert every responsibility in my resume into a measurable achievement. Replace task-based statements with result-driven bullet points using metrics, outcomes, and business impact. Resume: {resume}.'''


def step_4_ats_alignment(resume: str, job_description: str) -> str:
    """ATS Keyword Alignment - aligns resume with job description."""
    return f'''Compare my resume with this job description and identify missing keywords. Rewrite my resume to align naturally with the role without keyword stuffing. Resume: {resume}. Job description: {job_description}.'''


def step_5_executive_tone(resume: str) -> str:
    """Executive Tone Upgrade - concise, confident language."""
    return f'''Rewrite my resume using concise, confident, executive-level language. Remove filler words, passive phrases, and generic statements while preserving full accuracy. Resume: {resume}.'''


def step_6_scan_optimization(resume: str) -> str:
    """10-Second Scan Optimization - improves structure and visual hierarchy."""
    return f'''Reformat my resume so the most impressive achievements and skills are visible within the first 10 seconds. Improve structure, visual hierarchy, and clarity throughout. Resume: {resume}.'''


def step_7_final_polish(resume: str) -> str:
    """Final Executive Polish - interview-ready document."""
    return f'''Act as a $500 an hour executive resume writer. Review my revised resume and refine it into a clean, high-impact, interview-ready document that communicates value immediately. Resume: {resume}.'''


# Step 2 needs the full resume with the new summary integrated. The prompt asks to "rewrite my professional summary"
# so the output should be the full resume with the new summary. We'll instruct Claude to return the complete resume.
STEP_2_SYSTEM = "Return the complete revised resume with the new professional summary integrated. Do not return only the summary - return the full resume document."

# Steps 3-7 output full resumes.
STEP_3_SYSTEM = "Return the complete revised resume with all responsibilities converted to achievements. Output the full resume document only."
STEP_4_SYSTEM = "Return the complete revised resume with ATS keywords aligned. Output the full resume document only."
STEP_5_SYSTEM = "Return the complete revised resume with executive tone. Output the full resume document only."
STEP_6_SYSTEM = "Return the complete revised resume with the new structure and hierarchy. Output the full resume document only."
STEP_7_SYSTEM = "Return the complete revised resume. Output the full resume document only."
