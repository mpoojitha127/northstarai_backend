"""
Recommendation Feed generator.

MVP deliberately uses deterministic rules rather than another AI call:
deadline proximity and progress-vs-time-elapsed are well-defined signals
that don't need a language model to detect, and rules are free, instant,
and debuggable. This can be upgraded to a periodic AI-driven pass later
(see docs/ROADMAP.md) once there's enough usage data to make LLM-generated
suggestions consistently better than the rules below.
"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.tracking import Recommendation


def generate_recommendations_for_user(db: Session, user_id: str) -> list[Recommendation]:
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    new_recs: list[Recommendation] = []
    today = date.today()

    for goal in goals:
        if goal.deadline:
            days_left = (goal.deadline - today).days
            if 0 <= days_left <= 3 and goal.progress_percent < 80:
                new_recs.append(
                    Recommendation(
                        user_id=user_id,
                        goal_id=goal.id,
                        kind="deadline",
                        message=(
                            f"'{goal.title}' is due in {days_left} day(s) and is only "
                            f"{goal.progress_percent}% complete. Consider narrowing scope to what's "
                            f"essential for launch."
                        ),
                    )
                )
            elif days_left < 0 and goal.status == "active":
                new_recs.append(
                    Recommendation(
                        user_id=user_id,
                        goal_id=goal.id,
                        kind="deadline",
                        message=(
                            f"'{goal.title}' passed its deadline. Update the deadline or mark it "
                            f"complete so your dashboard reflects reality."
                        ),
                    )
                )

        if goal.progress_percent == 0:
            days_since_created = (
                (datetime.utcnow().date() - goal.created_at.date()).days if goal.created_at else 0
            )
            if days_since_created >= 5:
                new_recs.append(
                    Recommendation(
                        user_id=user_id,
                        goal_id=goal.id,
                        kind="validation",
                        message=(
                            f"'{goal.title}' has had no recorded progress in {days_since_created} days. "
                            f"Is this still a priority, or should it be archived?"
                        ),
                    )
                )

    for rec in new_recs:
        db.add(rec)
    if new_recs:
        db.commit()
    return new_recs
