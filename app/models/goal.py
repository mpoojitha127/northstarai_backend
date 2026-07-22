import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import GoalPriority, GoalStatus


def _uuid() -> str:
    return str(uuid.uuid4())


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String, default="general")
    priority: Mapped[str] = mapped_column(String, default=GoalPriority.MEDIUM.value)
    status: Mapped[str] = mapped_column(String, default=GoalStatus.ACTIVE.value)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_percent: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="goals")
    conversations = relationship("Conversation", back_populates="primary_goal")
    progress_logs = relationship("ProgressLog", back_populates="goal", cascade="all, delete-orphan")
    warnings = relationship("Warning", back_populates="goal", cascade="all, delete-orphan")
