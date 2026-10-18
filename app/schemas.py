from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(default="u_001", min_length=1, max_length=100)


class ActionDecision(BaseModel):
    action: str
    reason: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class ChatResponse(BaseModel):
    answer: str
    context: list[dict[str, Any]]
    decision: ActionDecision | None = None
    pending_action_id: str | None = None


class ConfirmRequest(BaseModel):
    approved: bool


class ActionResponse(BaseModel):
    action_id: str
    status: Literal["approved", "rejected", "executed"]
    result: dict[str, Any] = Field(default_factory=dict)
