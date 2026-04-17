"""Tests for the LLM inference service."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.inference_service import InferenceService, FindingResult, _validate_finding


VALID_FINDING_DICT = {
    "file_path": "auth.py",
    "line_number": 12,
    "category": "sql_injection",
    "severity": "critical",
    "confidence": 0.95,
    "summary": "Raw SQL constructed via f-string",
    "explanation": "User input is directly interpolated into SQL query.",
    "suggested_fix": "Use parameterized queries: conn.execute(query, (username,))",
}


def test_validate_finding_valid():
    result = _validate_finding(VALID_FINDING_DICT)
    assert result is not None
    assert result.category == "sql_injection"
    assert result.severity == "critical"
    assert result.confidence == 0.95


def test_validate_finding_invalid_category():
    bad = {**VALID_FINDING_DICT, "category": "fake_category"}
    assert _validate_finding(bad) is None


def test_validate_finding_invalid_severity():
    bad = {**VALID_FINDING_DICT, "severity": "extreme"}
    assert _validate_finding(bad) is None


def test_finding_result_to_dict():
    finding = FindingResult(**VALID_FINDING_DICT)
    d = finding.to_dict()
    assert d["file_path"] == "auth.py"
    assert d["category"] == "sql_injection"


@pytest.mark.asyncio
async def test_analyze_chunk_returns_findings():
    """analyze_chunk should parse model JSON output into FindingResult objects."""
    mock_content = json.dumps([VALID_FINDING_DICT])
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": mock_content}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        svc = InferenceService()
        findings = await svc.analyze_chunk(
            "def login(u):\n    query = f'SELECT * WHERE u={u}'", context=[]
        )

    assert len(findings) == 1
    assert findings[0].category == "sql_injection"
    assert findings[0].severity == "critical"


@pytest.mark.asyncio
async def test_analyze_chunk_returns_empty_on_invalid_json():
    """Malformed JSON from model should return empty list, not raise."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "NOT JSON { } {"}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        svc = InferenceService()
        findings = await svc.analyze_chunk("some code", context=[])

    assert findings == []


@pytest.mark.asyncio
async def test_analyze_chunk_returns_empty_list_response():
    """Model returning [] means no issues found — should be valid."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "[]"}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        svc = InferenceService()
        findings = await svc.analyze_chunk("clean_code()", context=[])

    assert findings == []
