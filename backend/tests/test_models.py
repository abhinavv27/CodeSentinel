"""Tests for SQLAlchemy models — enums and structure."""
import pytest
from app.models.finding import Finding, Severity, Category
from app.models.feedback import Feedback, FeedbackType


def test_severity_enum_values():
    assert Severity.CRITICAL.value == "critical"
    assert Severity.WARNING.value == "warning"
    assert Severity.INFO.value == "info"


def test_category_enum_has_all_12_patterns():
    expected = {
        "sql_injection",
        "hardcoded_secret",
        "missing_null_check",
        "race_condition",
        "exception_swallowing",
        "n_plus_1",
        "insecure_deserialization",
        "ssrf",
        "missing_input_validation",
        "dead_code",
        "style_violation",
        "unbounded_loop",
    }
    actual = {c.value for c in Category}
    assert actual == expected, f"Missing: {expected - actual}"


def test_feedback_type_enum():
    assert FeedbackType.ACCEPT.value == "accept"
    assert FeedbackType.REJECT.value == "reject"
    assert FeedbackType.FALSE_POSITIVE.value == "false_positive"
