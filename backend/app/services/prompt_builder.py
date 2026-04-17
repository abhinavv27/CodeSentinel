import json
SYSTEM_PROMPT = """You are CodeSentinel, an expert code reviewer. Analyze the provided code diff and identify issues.

For each issue found, output a JSON array of findings. If no issues are found, return an empty array [].

Each finding must be a JSON object with these exact fields:
- file_path: string (path to the file with the issue)
- line_number: integer (the line where the issue occurs, use the + line numbers from the diff)
- category: one of [sql_injection, hardcoded_secret, missing_null_check, race_condition, exception_swallowing, n_plus_1, insecure_deserialization, ssrf, missing_input_validation, dead_code, style_violation, unbounded_loop]
- severity: one of [critical, warning, info]
- confidence: float between 0.0 and 1.0
- summary: string (one sentence, max 100 chars, describe the specific issue concisely)
- explanation: string (3-5 sentences explaining why this is a problem and its potential impact)
- suggested_fix: string (a concrete code snippet showing the fix, or null if not applicable)

IMPORTANT RULES:
- Only flag genuinely problematic code, not style preferences
- critical = security vulnerability or data loss risk
- warning = bug-prone or performance issue
- info = style, naming, or minor improvement
- Be specific: cite the exact variable/function name and line
- Output ONLY a valid JSON array. No markdown, no explanation, no text before or after the JSON."""


def build_user_prompt(diff_chunk: str, context_snippets: list[str], feedback_memory: list[dict] = None, security_context: str = "") -> str:
    """Build the user message prompt combining diff chunk, RAG context, feedback, and security alerts."""
    context_section = ""
    if context_snippets:
        context_section = (
            "\n\n### Relevant Codebase Context (for additional understanding):\n"
            + "\n---\n".join(s for s in context_snippets[:3] if s.strip())
        )
    
    feedback_section = ""
    if feedback_memory:
        feedback_section = "\n\n### Institutional Memory (Past review feedback):\n"
        for f in feedback_memory:
            status = "REJECTED (False Positive)" if f['type'] in ["reject", "false_positive"] else "ACCEPTED"
            feedback_section += f"- Past finding ({status}): {f['summary']} - Reason: {f['explanation']}\n"

    return (
        f"### Code Diff to Review:\n```\n{diff_chunk}\n```"
        f"{context_section}"
        f"{feedback_section}"
        f"{security_context}"
        f"\n\nAnalyze the diff above. Return findings as a JSON array:"
    )


def build_critique_prompt(diff_chunk: str, findings: list[dict]) -> str:
    """Build a prompt asking the model to critique and filter its own previous findings."""
    return (
        f"### Code Diff to Review:\n```\n{diff_chunk}\n```\n\n"
        f"### Your Initial Findings:\n```json\n{json.dumps(findings, indent=2)}\n```\n\n"
        f"CRITICAL ANALYST TASK:\n"
        f"1. Review each finding above against the diff.\n"
        f"2. IDENTIFY FALSE POSITIVES: Is the flag incorrect? Is it a standard pattern? Is the logic actually safe?\n"
        f"3. ADJUST CONFIDENCE: If the finding is likely valid but slightly uncertain, lower the confidence.\n"
        f"4. REMOVE: Delete any finding that you now believe is a False Positive.\n"
        f"5. RETURN: Output the refined JSON array of findings only."
    )
