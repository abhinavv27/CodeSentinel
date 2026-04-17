import yaml
import structlog
from typing import List, Dict, Any
from pathlib import Path

logger = structlog.get_logger()

class PolicyService:
    """
    Enforces repository-specific governance policies defined in .codesentinel.yaml.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.config_path = self.repo_path / ".codesentinel.yaml"
        self.policies = self._load_config()

    def _load_config(self) -> List[Dict]:
        """Loads and parses the .codesentinel.yaml config."""
        if not self.config_path.exists():
            logger.info("policy_config_not_found", path=str(self.config_path))
            return []
        
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                return config.get("policies", [])
        except Exception as e:
            logger.error("policy_config_load_failed", error=str(e))
            return []

    def evaluate_findings(self, findings: List[Dict]) -> List[Dict]:
        """
        Enriches findings with policy results (e.g., 'level': 'error' or 'warning').
        """
        if not self.policies:
            return findings

        for finding in findings:
            finding["policy_status"] = "pass"
            finding["policy_violations"] = []

            for policy in self.policies:
                if self._match_policy(finding, policy):
                    finding["policy_status"] = "fail"
                    finding["policy_violations"].append(policy.get("name"))
                    # If any policy is 'error', the finding is promoted to a blocker
                    if policy.get("level") == "error":
                        finding["is_blocker"] = True
        
        return findings

    def _match_policy(self, finding: Dict, policy: Dict) -> bool:
        """
        Simple rule matching logic.
        Supported fields: severity, category, file_path.
        """
        query = policy.get("query", "")
        
        # v1: Simple keyword matching or field matching
        # Example: "severity == 'critical'"
        try:
            # Dangerous if using eval(), but we'll parse it safely or use a DSL
            # For now, we'll support a few hardcoded patterns
            severity = finding.get("severity", "").lower()
            category = finding.get("category", "").lower()
            path = finding.get("file_path", "")

            # If query is 'severity == critical'
            if "severity == 'critical'" in query and severity == "critical":
                return True
            if "severity == 'high'" in query and severity == "high":
                return True
            if "category == 'security'" in query and category == "security":
                return True
            
            # Path based
            if "path_matches" in policy:
                import re
                if re.search(policy["path_matches"], path):
                    return True
                    
        except Exception as e:
            logger.error("policy_match_failed", error=str(e))
            
        return False
