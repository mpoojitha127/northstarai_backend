from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.goal import Goal
from app.models.tracking import ProgressLog
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"])


def _get_owned_goal(db: Session, goal_id: str, user: User) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.get("", response_model=list[GoalOut])
def list_goals(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Goal]:
    query = db.query(Goal).filter(Goal.user_id == current_user.id)
    if status_filter:
        query = query.filter(Goal.status == status_filter)
    return query.order_by(Goal.created_at.desc()).all()


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    goal = Goal(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority.value,
        deadline=payload.deadline,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    db.add(ProgressLog(goal_id=goal.id, event_type="created", detail=f"Goal '{goal.title}' created."))
    db.commit()
    return goal


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Goal:
    return _get_owned_goal(db, goal_id, current_user)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    goal = _get_owned_goal(db, goal_id, current_user)
    update_data = payload.model_dump(exclude_unset=True)

    progress_changed = "progress_percent" in update_data and update_data["progress_percent"] != goal.progress_percent

    for field, value in update_data.items():
        setattr(goal, field, value.value if hasattr(value, "value") else value)

    db.commit()
    db.refresh(goal)

    if progress_changed:
        db.add(
            ProgressLog(
                goal_id=goal.id,
                event_type="progress",
                detail=f"Progress updated to {goal.progress_percent}%.",
                progress_percent=goal.progress_percent,
            )
        )
        db.commit()

    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    goal = _get_owned_goal(db, goal_id, current_user)
    db.delete(goal)
    db.commit()


@router.post("/{goal_id}/archive", response_model=GoalOut)
def archive_goal(
    goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Goal:
    goal = _get_owned_goal(db, goal_id, current_user)
    goal.status = "archived"
    db.commit()
    db.refresh(goal)
    return goal
