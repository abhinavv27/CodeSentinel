import enum
import uuid
from datetime import datetime
from sqlalchemy import Enum as SAEnum, String, Integer, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Category(str, enum.Enum):
    SQL_INJECTION = "sql_injection"
    HARDCODED_SECRET = "hardcoded_secret"
    MISSING_NULL_CHECK = "missing_null_check"
    RACE_CONDITION = "race_condition"
    EXCEPTION_SWALLOWING = "exception_swallowing"
    N_PLUS_1 = "n_plus_1"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    SSRF = "ssrf"
    MISSING_INPUT_VALIDATION = "missing_input_validation"
    DEAD_CODE = "dead_code"
    STYLE_VIOLATION = "style_violation"
    UNBOUNDED_LOOP = "unbounded_loop"


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[Category] = mapped_column(
        SAEnum(Category, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    severity: Mapped[Severity] = mapped_column(
        SAEnum(Severity, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0–1.0
    summary: Mapped[str] = mapped_column(String(256), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=True)
    github_comment_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pull_request: Mapped["PullRequest"] = relationship(  # type: ignore[name-defined]
        "PullRequest", back_populates="findings"
    )
    feedbacks: Mapped[list] = relationship(
        "Feedback", back_populates="finding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Finding {self.category} [{self.severity}] @ {self.file_path}:{self.line_number}>"
