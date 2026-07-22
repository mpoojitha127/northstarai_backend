from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    goal_id: str | None = None
    message: str


class AlignmentResult(BaseModel):
    verdict: str
    reason: str
    alternative: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    alignment: AlignmentResult
    reflection_notes: list[str] = []


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    alignment_verdict: str | None
    alignment_reason: str | None
    alignment_alternative: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    title: str
    primary_goal_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
