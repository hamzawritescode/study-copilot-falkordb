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
        action = PendingAction(f"act_{uuid.uuid4().hex[:10]}", user_id, name, parameters, reason, datetime.datetime.now(datetime.UTC).isoformat())
        self.pending[action.action_id] = action
        return action

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
        return {"message": "Study plan created", "rows": rows}

    def _recommend_next_topic(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.next_topics(user_id)
        return {"message": "Next topic recommended", "rows": rows[:1]}

    def _mark_resource_complete(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.mark_resource_complete(user_id, parameters["resource_id"])
        return {"message": "Resource marked complete", "rows": rows}

    def _record_quiz_attempt(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.record_quiz_attempt(user_id, parameters["quiz_id"], float(parameters["score"]))
        return {"message": "Quiz attempt recorded", "rows": rows}

    def _update_progress(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.record_progress(user_id, parameters["topic_id"], float(parameters["mastery"]))
        return {"message": "Progress updated", "rows": rows}

    def _generate_practice_questions(self, user_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.practice_questions(parameters.get("topic_id"))
        return {"message": "Practice questions generated", "rows": rows}
