import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from typing import Optional
from app.core.config import get_settings
from app.tasks.review_tasks import enqueue_pr_review
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.finding import Finding
from app.models.feedback import Feedback, FeedbackType
import structlog

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()

# PR actions that should trigger a review
TRIGGER_ACTIONS = {"opened", "synchronize", "reopened"}


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify the GitHub HMAC-SHA256 webhook signature."""
    if not settings.github_webhook_secret:
        # Dev mode: skip signature verification
        return True
    mac = hmac.new(
        settings.github_webhook_secret.encode(), payload, hashlib.sha256
    )
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


async def process_reaction(payload: dict) -> None:
    """Map GitHub reactions to CodeSentinel feedback."""
    action = payload.get("action", "")
    content = payload.get("reaction", {}).get("content", "")
    comment_data = payload.get("pull_request_review_comment", {})
    comment_id = comment_data.get("id")

    if not comment_id:
        return

    # Map reactions: +1 -> accept, -1 -> false_positive
    feedback_type = None
    if content == "+1":
        feedback_type = FeedbackType.ACCEPT
    elif content == "-1":
        feedback_type = FeedbackType.FALSE_POSITIVE

    if action == "created" and feedback_type:
        async with AsyncSessionLocal() as db:
            finding = await db.scalar(
                select(Finding).where(Finding.github_comment_id == comment_id)
            )
            if finding:
                new_feedback = Feedback(
                    finding_id=finding.id,
                    author=payload.get("sender", {}).get("login", "unknown"),
                    feedback_type=feedback_type,
                )
                db.add(new_feedback)
                await db.commit()
                logger.info(
                    "feedback_recorded",
                    finding_id=finding.id,
                    type=feedback_type,
                    author=new_feedback.author,
                )


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """Receive GitHub webhook events and dispatch PR reviews or process feedback."""
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256 or ""):
        logger.warning("webhook_invalid_signature")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    if x_github_event == "ping":
        return {"status": "pong"}

    payload = json.loads(body)
    action = payload.get("action", "")

    if x_github_event == "pull_request" and action in TRIGGER_ACTIONS:
        logger.info(
            "webhook_pr_received",
            repo=payload.get("repository", {}).get("full_name"),
            pr=payload.get("pull_request", {}).get("number"),
            action=action,
        )
        background_tasks.add_task(enqueue_pr_review, payload)
    
    elif x_github_event == "reaction":
        background_tasks.add_task(process_reaction, payload)
    
    elif x_github_event in ["issue_comment", "pull_request_review_comment"]:
        comment_body = payload.get("comment", {}).get("body", "").lower()
        if "/fix" in comment_body:
             from app.tasks.review_tasks import run_remediation
             
             # Extract finding from the context of the comment
             # Normally we'd look at 'in_reply_to_id' for review comments
             reply_id = payload.get("comment", {}).get("in_reply_to_id")
             if reply_id:
                  async with AsyncSessionLocal() as db:
                       finding = await db.scalar(select(Finding).where(Finding.github_comment_id == reply_id))
                       if finding:
                            run_remediation.delay(
                                 finding_id=str(finding.id),
                                 installation_id=payload.get("installation", {}).get("id")
                            )
                            logger.info("remediation_triggered", finding_id=finding.id)

    return {"status": "accepted", "event": x_github_event, "action": action}
