import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class FeedbackType(str, enum.Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FALSE_POSITIVE = "false_positive"


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(
        SAEnum(FeedbackType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    finding: Mapped["Finding"] = relationship(  # type: ignore[name-defined]
        "Finding", back_populates="feedbacks"
    )

    def __repr__(self) -> str:
        return f"<Feedback {self.feedback_type} on finding {self.finding_id}>"
