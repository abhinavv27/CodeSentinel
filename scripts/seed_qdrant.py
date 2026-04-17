#!/usr/bin/env python
"""
Seed Qdrant with all source files from a local repository.

Usage:
    python scripts/seed_qdrant.py --repo-path /path/to/repo [--extensions .py .js .ts]

This script should be run once per repository before CodeSentinel starts reviewing PRs.
It indexes all source files' content as vector embeddings into Qdrant for RAG retrieval.
"""
import argparse
import pathlib
import sys
import os

# Add backend to path so we can import app
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from app.services.rag_service import RagService

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".java", ".rb", ".rs",
    ".cpp", ".c", ".h", ".cs",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Qdrant with repository code")
    parser.add_argument("--repo-path", required=True, help="Path to the repository root")
    parser.add_argument("--repo-name", help="GitHub full name (e.g. owner/repo) to update DB metadata")
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=list(DEFAULT_EXTENSIONS),
        help="File extensions to index (e.g., .py .js)",
    )
    parser.add_argument("--dry-run", action="store_true", help="List files without indexing")
    args = parser.parse_args()

    repo = pathlib.Path(args.repo_path).resolve()
    if not repo.exists():
        print(f"ERROR: Repository path does not exist: {repo}")
        sys.exit(1)

    extensions = set(args.extensions)
    svc = RagService()

    # Collect files
    files = []
    for f in repo.rglob("*"):
        if f.is_file() and f.suffix in extensions:
            if not any(part in SKIP_DIRS for part in f.parts):
                files.append(f)

    print(f"Found {len(files)} files to index in {repo}")

    if args.dry_run:
        for f in files:
            print(f"  {f.relative_to(repo)}")
        return

    success = 0
    errors = 0
    for f in files:
        rel_path = str(f.relative_to(repo))
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if content.strip():
                svc.index_file(rel_path, content)
                print(f"  ✓ {rel_path}")
                success += 1
            else:
                print(f"  ○ {rel_path} (empty)")
        except Exception as e:
            print(f"  ✗ {rel_path}: {e}")
            errors += 1

    # Optional: Update Repository table in DB
    repo_name = getattr(args, "repo_name", None)
    if repo_name and success > 0:
        from app.core.database import AsyncSessionLocal
        from app.models.repository import Repository
        from sqlalchemy import select
        import asyncio
        from datetime import datetime

        async def update_db():
            async with AsyncSessionLocal() as db:
                r = await db.scalar(select(Repository).where(Repository.github_full_name == repo_name))
                if r:
                    r.indexed_at = datetime.utcnow()
                    await db.commit()
                    print(f"Updated database: {repo_name} indexed_at set to now.")
        
        asyncio.run(update_db())

    print(f"\nDone: {success} indexed, {errors} errors")


if __name__ == "__main__":
    main()
