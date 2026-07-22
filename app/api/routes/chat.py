from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db

from app.models.user import User
from app.models.goal import Goal
from app.models.conversation import Conversation, Message
from app.models.tracking import ProgressLog
from app.models.tracking import Warning as WarningModel

from app.schemas.chat import (
    AlignmentResult,
    ChatRequest,
    ChatResponse,
    ConversationOut,
    MessageOut,
)

from app.services import memory_service
from app.services.ai_provider import get_ai_provider
from app.services.context_builder import build_context
from app.services.northstar_layer import northstar

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

provider = get_ai_provider()


@router.post("", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:

    # ==========================================================
    # Resolve Existing Conversation or Create New One
    # ==========================================================

    if payload.conversation_id:

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    else:

        conversation = Conversation(
            user_id=current_user.id,
            primary_goal_id=payload.goal_id,
            title=payload.message[:60],
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # ==========================================================
    # Resolve Goal
    # ==========================================================

    goal = None

    if conversation.primary_goal_id:

        goal = (
            db.query(Goal)
            .filter(
                Goal.id == conversation.primary_goal_id,
                Goal.user_id == current_user.id,
            )
            .first()
        )

    # ==========================================================
    # Save User Message
    # ==========================================================

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # ==========================================================
    # Retrieve Relevant Memories
    # ==========================================================

    memory_texts = []

    if goal:

        memories = memory_service.query_memory(
            current_user.id,
            payload.message,
            n_results=5,
        )

        memory_texts = [
            memory["text"]
            for memory in memories
        ]

    # ==========================================================
    # Build Conversation History
    # ==========================================================

    history = []

    for msg in conversation.messages:

        history.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    # ==========================================================
    # Build Context for Main AI
    # ==========================================================

    context = build_context(
        goal_title=goal.title if goal else None,
        goal_description=goal.description if goal else None,
        conversation_history=history,
        memories=memory_texts,
        current_request=payload.message,
    )

    # ==========================================================
    # Generate Original AI Response
    # ==========================================================

    print("STEP 1 - Calling Main AI")

    original_response = provider.generate(
        system_prompt=context.system_prompt,
        user_prompt=context.user_prompt,
    )

    print("STEP 2 - Main AI Finished")
    print("STEP 3 - Calling NorthStar")
    # ==========================================================
    # NorthStar Analysis
    # ==========================================================

    analysis = northstar.analyze(
        goal=goal.title if goal else "No goal defined",
        user_prompt=payload.message,
        ai_response=original_response,
    )

    print("STEP 4 - NorthStar Finished")

    # ==========================================================
    # Final Response
    # ==========================================================

    answer_text = analysis.enhanced_response

    # ==========================================================
    # Save Assistant Message
    # ==========================================================

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_text,
        alignment_verdict=analysis.alignment.lower().replace(" ", "_"),
        alignment_reason=analysis.reason,
        alignment_alternative=analysis.suggestion,
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # ==========================================================
    # Save Semantic Memory
    # ==========================================================

    if goal:

        memory_service.add_memory(
            user_id=current_user.id,
            memory_id=user_message.id,
            text=f"User Request: {payload.message}",
            metadata={
                "goal_id": goal.id,
                "type": "user_request",
            },
        )

        memory_service.add_memory(
            user_id=current_user.id,
            memory_id=assistant_message.id,
            text=f"NorthStar Response: {answer_text}",
            metadata={
                "goal_id": goal.id,
                "type": "assistant_response",
            },
        )

    # ==========================================================
    # Log Goal Progress
    # ==========================================================

    if goal and analysis.alignment.lower() != "aligned":

        warning = WarningModel(
            goal_id=goal.id,
            message_id=assistant_message.id,
            verdict=analysis.alignment.lower().replace(" ", "_"),
            reason=analysis.reason,
            alternative=analysis.suggestion,
        )

        db.add(warning)

        progress = ProgressLog(
            goal_id=goal.id,
            event_type="warning",
            detail=analysis.reason,
        )

        db.add(progress)

        db.commit()

    elif goal:

        progress = ProgressLog(
            goal_id=goal.id,
            event_type="decision",
            detail=payload.message[:200],
        )

        db.add(progress)

        db.commit()
    # ==========================================================
    # Return Response
    # ==========================================================

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        content=answer_text,
        alignment=AlignmentResult(
            verdict=analysis.alignment,
            reason=analysis.reason,
            alternative=analysis.suggestion,
        ),
        reflection_notes=[],
    )


# ==========================================================
# List Conversations
# ==========================================================

@router.get(
    "/conversations",
    response_model=list[ConversationOut],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Conversation]:

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id,
        )
        .order_by(
            Conversation.updated_at.desc(),
        )
        .all()
    )

    return conversations


# ==========================================================
# Get Messages of a Conversation
# ==========================================================

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageOut],
)
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Message]:

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation.messages