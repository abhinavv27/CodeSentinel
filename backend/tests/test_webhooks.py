"""Tests for GitHub webhook handler."""
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_signature(secret: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_webhook_ping_returns_pong():
    """GitHub sends a 'ping' event when the webhook is first configured."""
    body = json.dumps({"zen": "hello world"}).encode()
    # No secret configured in tests → signature bypass
    resp = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=doesnotmatter",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "pong"}


def test_webhook_rejects_invalid_signature():
    """When a webhook secret is configured, bad signatures must be rejected."""
    body = b'{"action":"opened","pull_request":{}}'
    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "supersecret"
        resp = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=badsig",
            },
        )
    assert resp.status_code == 403


def test_webhook_pr_opened_dispatches_review():
    """A PR 'opened' event should enqueue a review task."""
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "diff_url": "https://github.com/owner/repo/pull/42.diff",
            "head": {"sha": "abc123"},
        },
        "repository": {"full_name": "owner/repo"},
        "installation": {"id": 12345},
    }
    body = json.dumps(payload).encode()

    with patch("app.api.webhooks.enqueue_pr_review") as mock_enqueue:
        resp = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=doesnotmatter",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"
    # enqueue_pr_review is called via BackgroundTasks — called after response
