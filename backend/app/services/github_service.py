import httpx
import yaml
import base64
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class GitHubService:
    """Helper for general GitHub API interactions."""
    
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, base_url="https://api.github.com")

    async def get_file_content(self, repo_full_name: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetch raw file content for a given path and branch/commit."""
        url = f"/repos/{repo_full_name}/contents/{path}?ref={ref}"
        try:
            response = await self.client.get(url)
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            content_b64 = data.get("content", "")
            if not content_b64:
                return None
            return base64.b64decode(content_b64).decode("utf-8")
        except Exception as e:
            logger.warning("github_fetch_file_failed", repo=repo_full_name, path=path, error=str(e))
            return None

    async def get_repo_config(self, repo_full_name: str) -> Dict[str, Any]:
        """Fetch and parse .codesentinel.yaml from the repository root."""
        content = await self.get_file_content(repo_full_name, ".codesentinel.yaml")
        if not content:
            return {}
        try:
            config = yaml.safe_load(content)
            return config if isinstance(config, dict) else {}
        except Exception as e:
            logger.warning("github_parse_config_failed", repo=repo_full_name, error=str(e))
            return {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
