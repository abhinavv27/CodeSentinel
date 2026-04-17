import httpx
import structlog
from typing import List, Dict
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class NotificationService:
    """
    Handles alerts to external platforms like Slack, Discord, or Teams.
    """

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url

    async def send_slack_alert(self, repo_name: str, pr_number: int, findings: List[Dict]):
        """
        Sends a formatted summary of findings to a Slack channel.
        """
        if not self.webhook_url:
            logger.info("slack_notification_skipped_no_webhook")
            return

        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        if critical_count == 0:
             # Only notify Slack for critical issues in v1
             return

        title = f"🚨 {critical_count} Critical Findings in {repo_name} PR #{pr_number}"
        
        # Build blocks for a premium Slack experience
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "content": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Repository:* {repo_name}\n*PR:* <https://github.com/{repo_name}/pull/{pr_number}|#{pr_number}>"
                }
            },
            {"type": "divider"}
        ]

        for finding in findings[:3]: # Show top 3 findings
             if finding.get("severity") == "critical":
                  blocks.append({
                      "type": "section",
                      "text": {
                          "type": "mrkdwn",
                          "text": f"*[{finding['category'].upper()}]* at line {finding['line_number']}\n>{finding['summary']}"
                      }
                  })

        if len(findings) > 3:
             blocks.append({
                 "type": "context",
                 "elements": [
                     {
                         "type": "mrkdwn",
                         "text": f"+ {len(findings) - 3} more findings. View full report in Dashboard."
                     }
                 ]
             })

        payload = {"blocks": blocks}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info("slack_notification_sent", repo=repo_name, pr=pr_number)
        except Exception as e:
            logger.error("slack_notification_failed", error=str(e))
