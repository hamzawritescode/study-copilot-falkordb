import re
from typing import Any, Iterable

from app.config import Settings
from app.repository import StudyRepository
from app.schemas import ActionDecision
from app.tools import ActionService


class StudyAgent:
    def __init__(self, repository: StudyRepository, actions: ActionService, settings: Settings):
        self.repository = repository
        self.actions = actions
        self.settings = settings

    def respond(self, user_id: str, message: str) -> dict[str, Any]:
        context = self.repository.user_context(user_id)
        available_minutes = self._available_minutes(context)
        requested_minutes = self._requested_minutes(message)
        minutes = requested_minutes if requested_minutes is not None else available_minutes
        candidates = self.repository.next_topics(user_id, minutes)
        blocked_method = getattr(self.repository, "blocked_topics", None)
        blocked = blocked_method(user_id, minutes) if blocked_method else []
        candidates = [self._with_evidence(user_id, row) for row in candidates]
        blocked = [self._with_evidence(user_id, row) for row in blocked]
        grounded = {
            "profile": context,
            "next_topics": candidates,
            "blocked_topics": blocked,
            "available_minutes": minutes,
        }
        decision = self._decide(message, grounded)
        pending_id = None
        if decision.requires_confirmation:
            pending = self.actions.stage(user_id, decision.action, decision.parameters, decision.reason)
            pending_id = pending.action_id
        evidence = self._recommendation_evidence(grounded, decision)
        blocked_candidates = self._blocked_evidence(user_id, blocked)
        return {
            "answer": self._answer(message, candidates, decision),
            "context": candidates + context + blocked,
            "decision": decision,
            "pending_action_id": pending_id,
            "evidence": evidence,
            "blocked_candidates": blocked_candidates,
        }

    def _decide(self, message: str, context: dict[str, Any]) -> ActionDecision:
        lower = message.lower()
        candidates = context["next_topics"]
        records = self._records(context)
        if "plan" in lower:
            requested_topic = self._requested_records(message, records, "topic")
            topic_ids = [requested_topic] if requested_topic else []
            if not topic_ids and "recommended" in lower and candidates:
                topic_ids = [self._value(candidates[0].get("candidate"), "id")]
            if not topic_ids:
                return self._clarification("Which topic ID or name should I include in the study plan?")
            return ActionDecision(action="create_study_plan", reason="The plan uses eligible topics ordered by prerequisite readiness and time budget.", parameters={"topic_ids": topic_ids}, requires_confirmation=True)
        if "resource" in lower or "complete" in lower:
            resource_id = self._requested_records(message, records, "resource")
            if not resource_id:
                return self._clarification("Which resource ID or name should I mark complete?")
            return ActionDecision(action="mark_resource_complete", reason="Marking a resource complete updates the learner-resource relationship.", parameters={"resource_id": resource_id}, requires_confirmation=True)
        if "quiz" in lower or "attempt" in lower:
            quiz_id = self._requested_records(message, records, "quiz")
            score = self._requested_score(message)
            missing = []
            if not quiz_id:
                missing.append("the quiz ID or name")
            if score is None:
                missing.append("the score between 0 and 1")
            if missing:
                return self._clarification(f"Please provide {self._join_missing(missing)}.")
            return ActionDecision(action="record_quiz_attempt", reason="Recording a quiz attempt adds a result connected to the quiz and learner.", parameters={"quiz_id": quiz_id, "score": score}, requires_confirmation=True)
        if "practice" in lower or "question" in lower:
            topic_id = self._requested_records(message, records, "topic")
            if not topic_id and "recommended" in lower and candidates:
                topic_id = self._value(candidates[0].get("candidate"), "id")
            if not topic_id:
                return self._clarification("Which topic ID or name should I use for practice questions?")
            return ActionDecision(action="generate_practice_questions", reason="Practice questions are grounded in the recommended topic and its connected quiz.", parameters={"topic_id": topic_id}, requires_confirmation=True)
        if "progress" in lower or "mastery" in lower:
            topic_id = self._requested_records(message, records, "topic")
            mastery = self._requested_mastery(message)
            missing = []
            if not topic_id:
                missing.append("the topic ID or name")
            if mastery is None:
                missing.append("the target mastery between 0 and 1")
            if missing:
                return self._clarification(f"Please provide {self._join_missing(missing)}.")
            return ActionDecision(action="update_progress", reason="Updating progress changes the learner's graph state and requires confirmation.", parameters={"topic_id": topic_id, "mastery": mastery}, requires_confirmation=True)
        return ActionDecision(action="recommend_next_topic", reason="Recommendation is grounded in prerequisite readiness, weak areas, and available time.", parameters={"topic_id": self._value(candidates[0].get("candidate"), "id") if candidates else None})

    def _answer(self, message: str, candidates: list[dict[str, Any]], decision: ActionDecision) -> str:
        if not decision.parameters and decision.reason:
            return decision.reason
        if decision.action == "create_study_plan":
            return "I found a prerequisite-ready study path. I can create a plan from the top eligible topics once you approve it."
        if decision.action == "update_progress":
            return "I can update your progress, but I need your explicit confirmation because this changes your learning record."
        if not candidates:
            return "I could not find an eligible topic in the current graph context. Try increasing your available study time or adding progress data."
        topic = self._value(candidates[0].get("candidate"), "name") or "the next topic"
        resource = self._value(candidates[0].get("resource"), "title")
        return f"Your next best step is {topic}. It is ready based on your prerequisite progress and fits your current time budget." + (f" Start with {resource}." if resource else "")

    def _recommendation_evidence(self, context: dict[str, Any], decision: ActionDecision) -> dict[str, Any] | None:
        candidates = context["next_topics"]
        topic_id = decision.parameters.get("topic_id")
        row = next((row for row in candidates if self._value(row.get("candidate"), "id") == topic_id), None)
        if not row:
            return None
        return {
            "recommended_topic": self._value(row, "candidate") or {},
            "reason": decision.reason,
            "prerequisite_path": row.get("evidence", []),
            "user_progress": [
                {
                    "topic": self._value(item, "t") or {},
                    "mastery": (self._value(item, "p") or {}).get("mastery"),
                }
                for item in context["profile"]
                if self._value(item, "p")
            ],
            "skill_gap": self._value(row, "gap"),
            "available_time": context["available_minutes"],
            "connected_resources": [self._value(row, "resource")] if self._value(row, "resource") else [],
            "connected_quizzes": [self._value(row, "quiz")] if self._value(row, "quiz") else [],
        }

    def _blocked_evidence(self, user_id: str, blocked: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        seen: set[str] = set()
        for row in blocked:
            topic = self._value(row, "candidate") or {}
            topic_id = topic.get("id")
            if not topic_id or topic_id in seen:
                continue
            seen.add(topic_id)
            prerequisite = self._value(row, "prerequisite") or {}
            progress = self._value(row, "mp") or {}
            mastery = progress.get("mastery", 0)
            result.append({
                "topic": topic,
                "reason": f"{prerequisite.get('name', 'A prerequisite')} mastery is {mastery:.2f}, below the 0.70 threshold.",
                "prerequisite_path": row.get("evidence", []),
            })
        return result

    def _records(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        return context["profile"] + context["next_topics"] + context["blocked_topics"]

    def _requested_records(self, message: str, records: Iterable[dict[str, Any]], kind: str) -> str | None:
        values = []
        for row in records:
            key = {"topic": "t", "resource": "resource", "quiz": "quiz"}[kind]
            value = self._value(row, key)
            if value:
                values.append(value)
            candidate = self._value(row, "candidate")
            if kind == "topic" and candidate:
                values.append(candidate)
        lower = message.lower()
        for value in values:
            value_id = str(value.get("id", "")).lower()
            value_name = str(value.get("name", value.get("title", ""))).lower()
            if value_id and value_id in lower or value_name and value_name in lower:
                return value.get("id")
        return None

    def _with_evidence(self, user_id: str, row: dict[str, Any]) -> dict[str, Any]:
        topic = self._value(row, "candidate")
        if not topic or not topic.get("id"):
            return row
        evidence_method = getattr(self.repository, "evidence_path", None)
        if not evidence_method:
            return row
        enriched = dict(row)
        enriched["evidence"] = evidence_method(user_id, topic["id"])
        return enriched

    @staticmethod
    def _requested_score(message: str) -> float | None:
        match = re.search(r"(?:score|got|result)\s*(?:of|is|=|:)?\s*(0(?:\.\d+)?|1(?:\.0+)?)\b", message.lower())
        return float(match.group(1)) if match else None

    @staticmethod
    def _requested_mastery(message: str) -> float | None:
        match = re.search(r"(?:mastery|progress|target)\s*(?:of|is|=|:)?\s*(0(?:\.\d+)?|1(?:\.0+)?)\b", message.lower())
        return float(match.group(1)) if match else None

    @staticmethod
    def _requested_minutes(message: str) -> int | None:
        match = re.search(r"\b(\d{1,3})\s*(?:minutes?|mins?)\b", message.lower())
        return int(match.group(1)) if match else None

    @staticmethod
    def _available_minutes(context: list[dict[str, Any]]) -> int:
        for row in context:
            user = row.get("u")
            if isinstance(user, dict) and user.get("available_minutes") is not None:
                return int(user["available_minutes"])
        raise ValueError("Your graph does not contain available study time.")

    @staticmethod
    def _join_missing(items: list[str]) -> str:
        return ", ".join(items[:-1]) + (" and " if len(items) > 1 else "") + items[-1]

    @staticmethod
    def _clarification(answer: str) -> ActionDecision:
        return ActionDecision(action="recommend_next_topic", reason=answer, parameters={})

    @staticmethod
    def _value(value: Any, key: str) -> Any:
        if isinstance(value, dict):
            return value.get(key)
        return None
