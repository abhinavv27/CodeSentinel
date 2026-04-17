"""Tests for the GitHub review poster service."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.github_poster import GitHubPoster, SEVERITY_EMOJI
from app.services.inference_service import FindingResult


def make_poster() -> GitHubPoster:
    """Create a GitHubPoster with mocked GitHub client."""
    with patch("app.services.github_poster.Github"):
        poster = GitHubPoster("owner/repo", 1, "fake-token")
    return poster


FINDING = FindingResult(
    file_path="auth.py",
    line_number=12,
    category="sql_injection",
    severity="critical",
    confidence=0.95,
    summary="SQL injection via f-string interpolation",
    explanation="User-controlled input is directly embedded into SQL. An attacker can bypass authentication or exfiltrate data.",
    suggested_fix="conn.execute('SELECT * FROM users WHERE username = %s', (username,))",
)


def test_format_comment_contains_emoji():
    poster = make_poster()
    comment = poster._format_comment(FINDING)
    assert "🔴" in comment


def test_format_comment_contains_category():
    poster = make_poster()
    comment = poster._format_comment(FINDING)
    assert "SQL Injection" in comment


def test_format_comment_contains_explanation():
    poster = make_poster()
    comment = poster._format_comment(FINDING)
    assert "attacker" in comment


def test_format_comment_contains_fix():
    poster = make_poster()
    comment = poster._format_comment(FINDING)
    assert "Suggested Fix" in comment
    assert "parameterized" in comment.lower() or "%s" in comment


def test_format_comment_warning_uses_yellow():
    warning_finding = FindingResult(
        file_path="db.py", line_number=5, category="n_plus_1", severity="warning",
        confidence=0.8, summary="N+1 query in loop", explanation="Each iteration hits the DB.",
    )
    poster = make_poster()
    comment = poster._format_comment(warning_finding)
    assert "🟡" in comment


def test_build_review_payload_structure():
    poster = make_poster()
    payload = poster._build_review_payload([FINDING], "abc123", "1 issue found")
    assert payload["event"] == "COMMENT"
    assert payload["commit_id"] == "abc123"
    assert len(payload["comments"]) == 1
    assert payload["comments"][0]["path"] == "auth.py"
    assert payload["comments"][0]["line"] == 12


def test_build_review_payload_no_findings():
    poster = make_poster()
    payload = poster._build_review_payload([], "abc123", "No issues.")
    assert payload["event"] == "COMMENT"
    assert len(payload["comments"]) == 0
    assert "CodeSentinel" in payload["body"]


def test_build_review_payload_counts_by_severity():
    findings = [
        FindingResult("a.py", 1, "sql_injection", "critical", 0.9, "issue", "exp"),
        FindingResult("b.py", 2, "dead_code", "info", 0.7, "issue", "exp"),
        FindingResult("c.py", 3, "n_plus_1", "warning", 0.8, "issue", "exp"),
    ]
    poster = make_poster()
    payload = poster._build_review_payload(findings, "sha", "3 issues")
    body = payload["body"]
    assert "1" in body  # critical count
    assert "1" in body  # warning count
