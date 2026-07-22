from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import GoalPriority, GoalStatus


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str = "general"
    priority: GoalPriority = GoalPriority.MEDIUM
    deadline: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: GoalPriority | None = None
    deadline: date | None = None
    status: GoalStatus | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)


class GoalOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    deadline: date | None
    progress_percent: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
