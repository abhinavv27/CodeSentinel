import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    # pending | processing | completed | failed
    status: Mapped[str] = mapped_column(String(64), default="pending")
    review_latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    # {"critical": 2, "warning": 5, "info": 1}
    findings_count: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    repository: Mapped["Repository"] = relationship(  # type: ignore[name-defined]
        "Repository", back_populates="pull_requests"
    )
    findings: Mapped[list] = relationship(
        "Finding", back_populates="pull_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PullRequest #{self.github_pr_number} [{self.status}]>"
