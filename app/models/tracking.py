import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Recommendation(Base):
    """Proactive suggestions surfaced on the dashboard's Recommendation Feed."""

    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    goal_id: Mapped[str | None] = mapped_column(ForeignKey("goals.id"), nullable=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String, default="general")  # deadline | balance | validation | general
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Warning(Base):
    """A Strategic Alignment Engine warning, logged for the Goal Timeline."""

    __tablename__ = "warnings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    goal_id: Mapped[str] = mapped_column(ForeignKey("goals.id"), nullable=False, index=True)
    message_id: Mapped[str | None] = mapped_column(ForeignKey("messages.id"), nullable=True)

    verdict: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    alternative: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal = relationship("Goal", back_populates="warnings")


class ProgressLog(Base):
    """Timeline entries: goal created, milestone hit, progress % changed, etc."""

    __tablename__ = "progress_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    goal_id: Mapped[str] = mapped_column(ForeignKey("goals.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String, nullable=False)  # created | decision | warning | task_done | progress
    detail: Mapped[str] = mapped_column(Text, default="")
    progress_percent: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal = relationship("Goal", back_populates="progress_logs")
