from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.feedback import Feedback, FeedbackType
from app.models.finding import Finding
import structlog

logger = structlog.get_logger()
router = APIRouter()


class FeedbackRequest(BaseModel):
    finding_id: str
    author: str
    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    status: str
    id: str


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackRequest, db: AsyncSession = Depends(get_db)
):
    """Submit feedback (accept / reject / false_positive) on a specific finding."""
    # Verify finding exists
    finding = await db.get(Finding, req.finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    fb = Feedback(
        finding_id=req.finding_id,
        author=req.author,
        feedback_type=req.feedback_type,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)

    # Index feedback in RAG for institutional memory
    try:
        from app.services.rag_service import RagService
        rag = RagService()
        finding_data = {
            "id": finding.id,
            "category": finding.category,
            "summary": finding.summary,
            "explanation": finding.explanation,
        }
        rag.index_feedback(finding_data, req.feedback_type.value)
    except Exception as e:
        logger.warning("feedback_rag_indexing_failed", error=str(e))

    logger.info(
        "feedback_recorded",
        finding_id=req.finding_id,
        type=req.feedback_type,
        author=req.author,
    )
    return {"status": "recorded", "id": fb.id}


@router.get("/{finding_id}")
async def get_finding_feedback(finding_id: str, db: AsyncSession = Depends(get_db)):
    """Get all feedback entries for a specific finding."""
    result = await db.execute(
        select(Feedback).where(Feedback.finding_id == finding_id)
    )
    feedbacks = result.scalars().all()
    return [
        {
            "id": f.id,
            "author": f.author,
            "feedback_type": f.feedback_type,
            "created_at": f.created_at.isoformat(),
        }
        for f in feedbacks
    ]
