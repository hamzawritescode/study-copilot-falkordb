import datetime
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from app.repository import StudyRepository

logger = logging.getLogger(__name__)


@dataclass
class PendingAction:
    action_id: str
    user_id: str
    name: str
    parameters: dict[str, Any]
    reason: str
    created_at: str


class ActionService:
    def __init__(self, repository: StudyRepository):
        self.repository = repository
        self.pending: dict[str, PendingAction] = {}
        self.audit_log: list[dict[str, Any]] = []
        self.handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "recommend_next_topic": self._recommend_next_topic,
            "create_study_plan": self._create_plan,
            "mark_resource_complete": self._mark_resource_complete,
            "record_quiz_attempt": self._record_quiz_attempt,
            "update_progress": self._update_progress,
            "generate_practice_questions": self._generate_practice_questions,
        }

    def stage(self, user_id: str, name: str, parameters: dict[str, Any], reason: str) -> PendingAction:
        if name not in self.handlers:
            raise ValueError(f"Unsupported action: {name}")
        self._validate_parameters(name, parameters)
        action = PendingAction(f"act_{uuid.uuid4().hex[:10]}", user_id, name, parameters, reason, datetime.datetime.now(datetime.UTC).isoformat())
        self.pending[action.action_id] = action
        return action

    @staticmethod
    def _validate_parameters(name: str, parameters: dict[str, Any]) -> None:
        if name == "create_study_plan":
            topic_ids = parameters.get("topic_ids")
            if not isinstance(topic_ids, list) or not topic_ids or not all(isinstance(topic_id, str) and topic_id for topic_id in topic_ids):
                raise ValueError("A study plan requires at least one valid topic")
        elif name == "mark_resource_complete":
            if not isinstance(parameters.get("resource_id"), str) or not parameters["resource_id"]:
                raise ValueError("A resource ID is required")
        elif name == "record_quiz_attempt":
            score = parameters.get("score")
            if not isinstance(parameters.get("quiz_id"), str) or not parameters["quiz_id"]:
                raise ValueError("A quiz ID is required")
            if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                raise ValueError("Quiz score must be between 0 and 1")
        elif name == "update_progress":
            mastery = parameters.get("mastery")
            if not isinstance(parameters.get("topic_id"), str) or not parameters["topic_id"]:
                raise ValueError("A topic ID is required")
            if not isinstance(mastery, (int, float)) or not 0 <= mastery <= 1:
                raise ValueError("Mastery must be between 0 and 1")
        elif name == "generate_practice_questions" and parameters.get("topic_id") is not None:
            if not isinstance(parameters["topic_id"], str) or not parameters["topic_id"]:
                raise ValueError("Topic ID must be a non-empty string")

    def confirm(self, action_id: str, approved: bool) -> dict[str, Any]:
        action = self.pending.pop(action_id, None)
        if not action:
            raise KeyError("Action no longer exists")
        entry = {"action_id": action.action_id, "name": action.name, "approved": approved, "at": datetime.datetime.now(datetime.UTC).isoformat()}
        self.audit_log.append(entry)
        if not approved:
            return {"status": "rejected", "result": {"message": "Action rejected by user"}}
        handler = self.handlers.get(action.name)
        if not handler:
            return {"status": "approved", "result": {"message": "Action approved but has no executor"}}
        return {"status": "executed", "result": handler(action.user_id, action.parameters)}

    def _create_plan(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.create_plan(user_id, parameters["topic_ids"], parameters.get("title", "My study plan"))
        if not rows:
            raise LookupError("No matching topics were found for the study plan")
        return {"message": "Study plan created", "rows": rows}

    def _recommend_next_topic(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.next_topics(user_id)
        return {"message": "Next topic recommended", "rows": rows[:1]}

    def _mark_resource_complete(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.mark_resource_complete(user_id, parameters["resource_id"])
        if not rows:
            raise LookupError("The requested resource was not found")
        return {"message": "Resource marked complete", "rows": rows}

    def _record_quiz_attempt(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.record_quiz_attempt(user_id, parameters["quiz_id"], float(parameters["score"]))
        if not rows:
            raise LookupError("The requested quiz was not found")
        return {"message": "Quiz attempt recorded", "rows": rows}

    def _update_progress(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.record_progress(user_id, parameters["topic_id"], float(parameters["mastery"]))
        if not rows:
            raise LookupError("The requested topic progress record was not found")
        return {"message": "Progress updated", "rows": rows}

    def _generate_practice_questions(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.practice_questions(parameters.get("topic_id"))
        return {"message": "Practice questions generated", "rows": rows}
