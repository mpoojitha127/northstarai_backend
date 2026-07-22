from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.conversation import Conversation
from app.models.goal import Goal
from app.models.tracking import ProgressLog, Recommendation
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, RecommendationOut, TimelineEntry
from app.services.recommendation_service import generate_recommendations_for_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardSummary:
    active_goals = db.query(Goal).filter(Goal.user_id == current_user.id, Goal.status == "active").all()
    avg_progress = (
        sum(g.progress_percent for g in active_goals) / len(active_goals) if active_goals else 0.0
    )

    recent_conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(5)
        .all()
    )

    # Refresh rule-based recommendations, then return current unread ones.
    generate_recommendations_for_user(db, current_user.id)
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.id, Recommendation.is_dismissed.is_(False))
        .order_by(Recommendation.created_at.desc())
        .limit(10)
        .all()
    )

    return DashboardSummary(
        active_goals=len(active_goals),
        average_progress=round(avg_progress, 1),
        recent_conversations=[
            {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in recent_conversations
        ],
        recommendations=[RecommendationOut.model_validate(r) for r in recs],
    )


@router.get("/goals/{goal_id}/timeline", response_model=list[TimelineEntry])
def get_goal_timeline(
    goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ProgressLog]:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        return []
    return (
        db.query(ProgressLog)
        .filter(ProgressLog.goal_id == goal_id)
        .order_by(ProgressLog.created_at.asc())
        .all()
    )


@router.post("/recommendations/{recommendation_id}/dismiss", status_code=204)
def dismiss_recommendation(
    recommendation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.id == recommendation_id, Recommendation.user_id == current_user.id)
        .first()
    )
    if rec:
        rec.is_dismissed = True
        db.commit()
