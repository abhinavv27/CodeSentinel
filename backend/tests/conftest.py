"""Pytest configuration and shared fixtures."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)
