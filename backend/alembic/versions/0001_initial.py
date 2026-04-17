"""Initial schema — repositories, pull_requests, findings, feedback.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("github_full_name", sa.String(256), nullable=False, unique=True),
        sa.Column("installation_id", sa.Integer(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "pull_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("repository_id", sa.String(36),
                  sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("author", sa.String(128), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="pending"),
        sa.Column("review_latency_ms", sa.Integer(), nullable=True),
        sa.Column("findings_count", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    severity_enum = sa.Enum("critical", "warning", "info", name="severity")
    category_enum = sa.Enum(
        "sql_injection", "hardcoded_secret", "missing_null_check",
        "race_condition", "exception_swallowing", "n_plus_1",
        "insecure_deserialization", "ssrf", "missing_input_validation",
        "dead_code", "style_violation", "unbounded_loop",
        name="category",
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pull_request_id", sa.String(36),
                  sa.ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("severity", severity_enum, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("summary", sa.String(256), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("github_comment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    feedback_enum = sa.Enum("accept", "reject", "false_positive", name="feedbacktype")
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("finding_id", sa.String(36),
                  sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author", sa.String(128), nullable=False),
        sa.Column("feedback_type", feedback_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Indexes for common queries
    op.create_index("ix_pull_requests_repository_id", "pull_requests", ["repository_id"])
    op.create_index("ix_findings_pull_request_id", "findings", ["pull_request_id"])
    op.create_index("ix_findings_severity", "findings", ["severity"])
    op.create_index("ix_findings_category", "findings", ["category"])
    op.create_index("ix_feedback_finding_id", "feedback", ["finding_id"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("findings")
    op.drop_table("pull_requests")
    op.drop_table("repositories")
    op.execute("DROP TYPE IF EXISTS feedbacktype")
    op.execute("DROP TYPE IF EXISTS category")
    op.execute("DROP TYPE IF EXISTS severity")
