from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from tokyoradar_shared.database import Base


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="qwen-plus")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", server_default="pending"
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    tool_calls: Mapped[int | None] = mapped_column(nullable=True)
    total_input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    total_output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    session_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
