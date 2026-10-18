import json
import logging
from typing import Any

import httpx

from app.config import Settings
from app.repository import StudyRepository
from app.schemas import ActionDecision
from app.tools import ActionService

logger = logging.getLogger(__name__)


class StudyAgent:
    def __init__(self, repository: StudyRepository, actions: ActionService, settings: Settings):
        self.repository = repository
        self.actions = actions
        self.settings = settings

    def respond(self, user_id: str, message: str) -> dict[str, Any]:
        context = self.repository.user_context(user_id)
        candidates = self.repository.next_topics(user_id)
        grounded = {"profile": context, "next_topics": candidates}
        decision = self._decide(message, grounded)
        pending_id = None
        if decision.requires_confirmation:
            pending = self.actions.stage(user_id, decision.action, decision.parameters, decision.reason)
            pending_id = pending.action_id
        return {"answer": self._answer(message, candidates, decision), "context": candidates + context, "decision": decision, "pending_action_id": pending_id}

    def _decide(self, message: str, context: dict[str, Any]) -> ActionDecision:
        lower = message.lower()
        candidates = context["next_topics"]
        if "plan" in lower:
            topic_ids = [self._value(row.get("candidate"), "id") for row in candidates[:3] if self._value(row.get("candidate"), "id")]
            return ActionDecision(action="create_study_plan", reason="The plan uses eligible topics ordered by prerequisite readiness and time budget.", parameters={"topic_ids": topic_ids, "title": "Aisha's next study sprint"}, requires_confirmation=True)
        if "resource" in lower or "complete" in lower:
            resource_id = self._value(candidates[0].get("resource"), "id") if candidates else None
            return ActionDecision(action="mark_resource_complete", reason="Marking a resource complete updates the learner-resource relationship.", parameters={"resource_id": resource_id}, requires_confirmation=True)
        if "quiz" in lower or "attempt" in lower:
            return ActionDecision(action="record_quiz_attempt", reason="Recording a quiz attempt adds a result connected to the quiz and learner.", parameters={"quiz_id": "q_data", "score": 0.8}, requires_confirmation=True)
        if "practice" in lower or "question" in lower:
            topic_id = self._value(candidates[0].get("candidate"), "id") if candidates else None
            return ActionDecision(action="generate_practice_questions", reason="Practice questions are grounded in the recommended topic and its connected quiz.", parameters={"topic_id": topic_id}, requires_confirmation=True)
        if "progress" in lower or "mastery" in lower:
            topic_id = self._value(candidates[0].get("candidate"), "id") if candidates else "t_data"
            return ActionDecision(action="update_progress", reason="Updating progress changes the learner's graph state and requires confirmation.", parameters={"topic_id": topic_id, "mastery": 0.75}, requires_confirmation=True)
        return ActionDecision(action="recommend_next_topic", reason="Recommendation is grounded in prerequisite readiness, weak areas, and available time.", parameters={"topic_id": self._value(candidates[0].get("candidate"), "id") if candidates else None})

    def _answer(self, message: str, candidates: list[dict[str, Any]], decision: ActionDecision) -> str:
        if decision.action == "create_study_plan":
            return "I found a prerequisite-ready study path. I can create a plan from the top eligible topics once you approve it."
        if decision.action == "update_progress":
            return "I can update your progress, but I need your explicit confirmation because this changes your learning record."
        if not candidates:
            return "I could not find an eligible topic in the current graph context. Try increasing your available study time or adding progress data."
        topic = self._value(candidates[0].get("candidate"), "name") or "the next topic"
        resource = self._value(candidates[0].get("resource"), "title")
        return f"Your next best step is {topic}. It is ready based on your prerequisite progress and fits your current time budget." + (f" Start with {resource}." if resource else "")

    @staticmethod
    def _value(value: Any, key: str) -> Any:
        if isinstance(value, dict):
            return value.get(key)
        return None
