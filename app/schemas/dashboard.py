from datetime import datetime

from pydantic import BaseModel


class RecommendationOut(BaseModel):
    id: str
    message: str
    kind: str
    is_dismissed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEntry(BaseModel):
    id: str
    event_type: str
    detail: str
    progress_percent: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    active_goals: int
    average_progress: float
    recent_conversations: list[dict]
    recommendations: list[RecommendationOut]
