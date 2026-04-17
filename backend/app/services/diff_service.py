from dataclasses import dataclass, field
from typing import List
import re


@dataclass
class DiffHunk:
    """Represents a single diff hunk (a contiguous block of changed lines in a file)."""

    file_path: str
    start_line: int
    context_before: List[str] = field(default_factory=list)
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Reconstruct a readable text block from the hunk."""
        all_lines = (
            self.context_before
            + self.removed_lines
            + self.added_lines
            + self.context_after
        )
        return "\n".join(all_lines)


def parse_diff(diff_text: str) -> List[DiffHunk]:
    """Parse a unified diff string into a list of DiffHunk objects.

    Preserves ±20 lines of surrounding context for each hunk.
    """
    hunks: List[DiffHunk] = []
    current_file = ""
    current_hunk: DiffHunk | None = None

    for line in diff_text.splitlines():
        # New file path
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+++ /dev/null"):
            current_file = "deleted_file"
        # New hunk header: @@ -a,b +c,d @@
        elif line.startswith("@@ "):
            if current_hunk is not None:
                hunks.append(current_hunk)
            match = re.search(r"\+(\d+)", line)
            start_line = int(match.group(1)) if match else 0
            current_hunk = DiffHunk(file_path=current_file, start_line=start_line)
        elif current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.added_lines.append(line)
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.removed_lines.append(line)
            else:
                # Context line
                if not current_hunk.added_lines and not current_hunk.removed_lines:
                    current_hunk.context_before.append(line)
                else:
                    current_hunk.context_after.append(line)

    if current_hunk is not None:
        hunks.append(current_hunk)

    return hunks


def chunk_hunks(hunks: List[DiffHunk], max_tokens: int = 4096) -> List[str]:
    """Group DiffHunks into text chunks that fit within the token limit.

    Uses a rough 4 characters-per-token estimate.
    """
    max_chars = max_tokens * 4
    chunks: List[str] = []
    current_chunk = ""

    for hunk in hunks:
        hunk_text = (
            f"### File: {hunk.file_path} (starting at line {hunk.start_line})\n"
            f"{hunk.to_text()}\n\n"
        )
        if len(current_chunk) + len(hunk_text) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = hunk_text
        else:
            current_chunk += hunk_text

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
