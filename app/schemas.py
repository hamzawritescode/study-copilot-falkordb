from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ActionName = Literal[
    "recommend_next_topic",
    "create_study_plan",
    "mark_resource_complete",
    "record_quiz_attempt",
    "update_progress",
    "generate_practice_questions",
]


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(default="u_001", min_length=1, max_length=100)


class ActionDecision(BaseModel):
    action: ActionName
    reason: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class EvidencePath(BaseModel):
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)


class RecommendationEvidence(BaseModel):
    recommended_topic: dict[str, Any] = Field(default_factory=dict)
    reason: str
    prerequisite_path: list[EvidencePath] = Field(default_factory=list)
    user_progress: list[dict[str, Any]] = Field(default_factory=list)
    skill_gap: dict[str, Any] | None = None
    available_time: int | None = None
    connected_resources: list[dict[str, Any]] = Field(default_factory=list)
    connected_quizzes: list[dict[str, Any]] = Field(default_factory=list)


class BlockedCandidate(BaseModel):
    topic: dict[str, Any] = Field(default_factory=dict)
    reason: str
    prerequisite_path: list[EvidencePath] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    context: list[dict[str, Any]]
    decision: ActionDecision | None = None
    pending_action_id: str | None = None
    evidence: RecommendationEvidence | None = None
    blocked_candidates: list[BlockedCandidate] = Field(default_factory=list)


class ConfirmRequest(BaseModel):
    approved: bool


class ActionResponse(BaseModel):
    action_id: str
    status: Literal["approved", "rejected", "executed"]
    result: dict[str, Any] = Field(default_factory=dict)
