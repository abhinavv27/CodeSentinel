from github import Github
from app.services.inference_service import FindingResult
import structlog

logger = structlog.get_logger()

SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🔵",
}

CATEGORY_LABELS = {
    "sql_injection": "SQL Injection",
    "hardcoded_secret": "Hardcoded Secret",
    "missing_null_check": "Missing Null Check",
    "race_condition": "Race Condition",
    "exception_swallowing": "Exception Swallowing",
    "n_plus_1": "N+1 Query",
    "insecure_deserialization": "Insecure Deserialization",
    "ssrf": "SSRF",
    "missing_input_validation": "Missing Input Validation",
    "dead_code": "Dead Code",
    "style_violation": "Style Violation",
    "unbounded_loop": "Unbounded Loop",
}


class GitHubPoster:
    """Posts batched inline review comments to a GitHub PR via PyGitHub."""

    def __init__(self, repo_full_name: str, pr_number: int, installation_token: str):
        self.gh = Github(installation_token)
        self.repo = self.gh.get_repo(repo_full_name)
        self.pr = self.repo.get_pull(pr_number)

    def _format_comment(self, finding: FindingResult) -> str:
        """Format a single finding as a rich Markdown comment body."""
        emoji = SEVERITY_EMOJI.get(finding.severity, "⚪")
        label = CATEGORY_LABELS.get(finding.category, finding.category.replace("_", " ").title())

        lines = [
            f"{emoji} **[{label}]** {finding.summary}",
            "",
            f"**Severity:** `{finding.severity}` &nbsp;·&nbsp; **Confidence:** `{finding.confidence:.0%}`",
            "",
            finding.explanation,
        ]
        if finding.suggested_fix:
            lines += [
                "",
                "**💡 Suggested Fix:**",
                f"```\n{finding.suggested_fix}\n```",
            ]
        lines += [
            "",
            "---",
            "_React 👍 to accept · 👎 to dismiss as false positive_",
        ]
        return "\n".join(lines)

    def _build_review_payload(
        self,
        findings: list[FindingResult],
        commit_sha: str,
        summary: str,
    ) -> dict:
        """Assemble the full GitHub review payload with inline comments."""
        comments = [
            {
                "path": f.file_path,
                "line": f.line_number,
                "body": self._format_comment(f),
            }
            for f in findings
        ]

        by_severity: dict[str, int] = {}
        for f in findings:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

        files_affected = len({f.file_path for f in findings})
        body = f"""## 🤖 CodeSentinel — Automated Pre-Review

{summary}

| Severity | Count |
|----------|-------|
| 🔴 Critical | {by_severity.get('critical', 0)} |
| 🟡 Warning  | {by_severity.get('warning', 0)} |
| 🔵 Info     | {by_severity.get('info', 0)} |

**Files reviewed:** {files_affected} file(s) with inline findings.

> *For human reviewer: The mechanical first-pass is complete. Focus your attention on architecture, business logic, and cross-cutting concerns.*
"""
        return {
            "event": "COMMENT",
            "body": body,
            "comments": comments,
            "commit_id": commit_sha,
        }

    def post_review(self, findings: list[FindingResult], commit_sha: str) -> list[int]:
        """Post all findings as a single batched GitHub PR review. Returns comment IDs."""
        if not findings:
            summary = "✅ No issues detected in this diff. Looks clean!"
            payload = self._build_review_payload([], commit_sha, summary)
            self.pr.create_review(**payload)
            return []

        summary = (
            f"Found **{len(findings)} issue(s)** across "
            f"{len({f.file_path for f in findings})} file(s)."
        )

        payload = self._build_review_payload(findings, commit_sha, summary)
        try:
            review = self.pr.create_review(**payload)
            # Retrieve the comments to get their IDs. We match them by path/line.
            # Note: order is generally preserved, but matching is safer.
            github_comments = list(review.get_comments())
            
            # Match finding results to their GitHub comment IDs
            ids = []
            for f in findings:
                # Find a matching comment (same file and line)
                match = next(
                    (c for c in github_comments if c.path == f.file_path and c.line == f.line_number),
                    None
                )
                if match:
                    ids.append(match.id)
                    github_comments.remove(match) # Ensure we don't reuse the same comment for duplicate findings on same line
                else:
                    ids.append(0) # Should not happen

            logger.info(
                "github_review_posted",
                pr=self.pr.number,
                findings=len(findings),
                commit=commit_sha[:8],
            )
            return ids
        except Exception as e:
            logger.error("github_review_post_failed", error=str(e), pr=self.pr.number)
            raise
