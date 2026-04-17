import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_full_name: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False
    )  # "owner/repo"
    installation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pull_requests: Mapped[list] = relationship(
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository {self.github_full_name}>"
