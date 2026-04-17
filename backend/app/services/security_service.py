import asyncio
import subprocess
import json
import os
import structlog
from typing import List, Dict

logger = structlog.get_logger()

class SecurityService:
    """Service for identifying vulnerabilities in project dependencies."""

    @staticmethod
    async def run_pip_audit(project_path: str, requirements_file: str = None) -> List[Dict]:
        """Runs pip-audit on the provided path or requirements file."""
        args = ["pip-audit", "--format", "json"]
        
        if requirements_file and os.path.exists(requirements_file):
            args.extend(["-r", requirements_file])
        else:
            req_file = os.path.join(project_path, "requirements.txt")
            if os.path.exists(req_file):
                args.extend(["-r", req_file])
            else:
                return []

        try:
            # Run pip-audit in a separate process
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and not stdout:
                logger.error("pip_audit_failed", error=stderr.decode())
                return []
            
            if not stdout:
                return []

            data = json.loads(stdout.decode())
            # pip-audit returns a list of dependency objects with 'vulnerabilities' key
            vulnerabilities = []
            for item in data.get("dependencies", []):
                if item.get("vulnerabilities"):
                    vulnerabilities.append({
                        "name": item["name"],
                        "version": item["version"],
                        "issues": item["vulnerabilities"]
                    })
            
            logger.info("security_audit_completed", count=len(vulnerabilities))
            return vulnerabilities

        except Exception as e:
            logger.error("security_audit_exception", error=str(e))
            return []

    @staticmethod
    def format_vulnerabilities_as_context(vulnerabilities: List[Dict]) -> str:
        """Formats the vulnerability list into a prompt-friendly context string."""
        if not vulnerabilities:
            return ""
        
        lines = ["\n### Project Dependency Vulnerabilities (Security Alert):"]
        for v in vulnerabilities:
            for issue in v["issues"]:
                lines.append(f"- {v['name']} ({v['version']}): {issue['id']} - {issue['description']}")
        
        return "\n".join(lines)
