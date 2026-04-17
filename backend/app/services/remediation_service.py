import os
import subprocess
from typing import List
import structlog

logger = structlog.get_logger()

class RemediationService:
    """
    Handles automated code fixes.
    Generates git patches and can potentially push commits to a branch.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    async def apply_fix(self, file_path: str, line_number: int, original_code: str, suggested_fix: str) -> bool:
        """
        Attempts to replace a code block with a suggested fix and stage the change.
        """
        full_path = os.path.join(self.repo_path, file_path)
        if not os.path.exists(full_path):
            logger.warning("fix_target_not_found", path=full_path)
            return False

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Simple heuristic replacement: find the line and check if it matches original_code
            # In a production system, we'd use a more robust AST-based or diff-based approach
            target_idx = line_number - 1
            if target_idx < len(lines):
                 # Verify context if possible
                 lines[target_idx] = suggested_fix + "\n"
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            logger.info("fix_applied_locally", file=file_path, line=line_number)
            return True
        except Exception as e:
            logger.error("fix_application_failed", error=str(e))
            return False

    def create_fix_branch(self, base_branch: str, fix_id: str) -> str:
        """Creates a new branch for the automated fix."""
        branch_name = f"codesentinel/fix-{fix_id}"
        try:
            subprocess.run(["git", "checkout", "-b", branch_name, base_branch], cwd=self.repo_path, check=True)
            return branch_name
        except subprocess.CalledProcessError as e:
            logger.error("branch_creation_failed", error=str(e))
            return base_branch

    def commit_and_push(self, branch_name: str, message: str):
        """Commits changes and pushes to origin."""
        try:
            subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_path, check=True)
            subprocess.run(["git", "push", "origin", branch_name], cwd=self.repo_path, check=True)
            logger.info("fix_pushed_to_remote", branch=branch_name)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("push_failed", error=str(e))
            return False
