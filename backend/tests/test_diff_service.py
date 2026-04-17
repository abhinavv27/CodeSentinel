"""Tests for diff parsing and chunking service."""
import pytest
from app.services.diff_service import parse_diff, chunk_hunks, DiffHunk

SAMPLE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index abc..def 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@ def login(username, password):
     conn = db.connect()
+    query = f"SELECT * FROM users WHERE username='{username}'"
+    result = conn.execute(query)
+    if not result:
+        return None
     return result.fetchone()
"""

MULTI_FILE_DIFF = """diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -5,3 +5,4 @@ def login(u):
     pass
+    secret = "abc123"
diff --git a/db.py b/db.py
--- a/db.py
+++ b/db.py
@@ -1,2 +1,3 @@ import db
+import os
 conn = db.connect()
"""


def test_parse_diff_returns_list():
    hunks = parse_diff(SAMPLE_DIFF)
    assert isinstance(hunks, list)


def test_parse_diff_extracts_file_path():
    hunks = parse_diff(SAMPLE_DIFF)
    assert len(hunks) == 1
    assert hunks[0].file_path == "src/auth.py"


def test_parse_diff_extracts_start_line():
    hunks = parse_diff(SAMPLE_DIFF)
    assert hunks[0].start_line == 10


def test_parse_diff_captures_added_lines():
    hunks = parse_diff(SAMPLE_DIFF)
    added = "\n".join(hunks[0].added_lines)
    assert "f\"SELECT" in added or "SELECT" in added


def test_parse_empty_diff():
    hunks = parse_diff("")
    assert hunks == []


def test_chunk_hunks_returns_list():
    hunks = parse_diff(SAMPLE_DIFF)
    chunks = chunk_hunks(hunks, max_tokens=4096)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1


def test_chunk_hunks_respects_token_limit():
    """Each chunk should be within ~4x max_tokens characters."""
    hunks = parse_diff(SAMPLE_DIFF)
    max_tokens = 100
    chunks = chunk_hunks(hunks, max_tokens=max_tokens)
    for chunk in chunks:
        assert len(chunk) <= max_tokens * 4 * 2  # allow some buffer


def test_chunk_hunks_includes_file_path():
    hunks = parse_diff(SAMPLE_DIFF)
    chunks = chunk_hunks(hunks)
    assert any("src/auth.py" in c for c in chunks)


def test_hunk_to_text_combines_lines():
    hunk = DiffHunk(
        file_path="foo.py",
        start_line=1,
        context_before=["context"],
        added_lines=["+new line"],
        removed_lines=["-old line"],
        context_after=["after"],
    )
    text = hunk.to_text()
    assert "context" in text
    assert "+new line" in text
    assert "-old line" in text
    assert "after" in text
