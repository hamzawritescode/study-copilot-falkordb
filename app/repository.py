from typing import Any

from app.database import GraphDatabase


class StudyRepository:
    def __init__(self, database: GraphDatabase):
        self.db = database

    def user_context(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id})-[:HAS_PROGRESS]->(p:Progress)-[:FOR_TOPIC]->(t:Topic)
        OPTIONAL MATCH (u)-[:HAS_GAP]->(g:SkillGap)-[:FOR_TOPIC]->(gt:Topic)
        RETURN u, p, t, g, gt
        """
        return self.db.query(query, {"user_id": user_id})

    def next_topics(self, user_id: str, available_minutes: int = 45) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id})-[:HAS_PROGRESS]->(p:Progress)-[:FOR_TOPIC]->(done:Topic)
        MATCH (candidate:Topic)
        WHERE candidate <> done
          AND candidate.estimated_minutes <= $minutes
          AND NOT EXISTS {
            MATCH (prerequisite:Topic)-[:PREREQUISITE_OF]->(candidate)
            WHERE NOT EXISTS {
              MATCH (u)-[:HAS_PROGRESS]->(mp:Progress)-[:FOR_TOPIC]->(prerequisite)
              WHERE mp.mastery >= 0.7
            }
          }
        OPTIONAL MATCH (u)-[:HAS_GAP]->(gap:SkillGap)-[:FOR_TOPIC]->(candidate)
        OPTIONAL MATCH (candidate)-[:HAS_RESOURCE]->(resource:Resource)
        RETURN candidate, gap, resource
        ORDER BY coalesce(gap.severity, 0) DESC, candidate.difficulty ASC
        """
        return self.db.query(query, {"user_id": user_id, "minutes": available_minutes})

    def evidence_path(self, user_id: str, topic_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH path=(u:User {id:$user_id})-[*1..4]-(t:Topic {id:$topic_id})
        RETURN [node IN nodes(path) | node] AS nodes, [rel IN relationships(path) | type(rel)] AS relationships
        LIMIT 3
        """
        return self.db.query(query, {"user_id": user_id, "topic_id": topic_id})

    def create_plan(self, user_id: str, topic_ids: list[str], title: str) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id})
        CREATE (u)-[:HAS_PLAN]->(plan:StudyPlan {id:$plan_id, title:$title, status:'active', created_at:$created_at})
        WITH plan
        UNWIND $topic_ids AS topic_id
        MATCH (topic:Topic {id:topic_id})
        CREATE (plan)-[:CONTAINS]->(item:StudyPlanItem {status:'planned', order:0})-[:TARGETS]->(topic)
        RETURN plan
        """
        import datetime
        import uuid
        return self.db.query(query, {"user_id": user_id, "topic_ids": topic_ids, "title": title, "plan_id": f"plan_{uuid.uuid4().hex[:8]}", "created_at": datetime.datetime.now(datetime.UTC).isoformat()})

    def record_progress(self, user_id: str, topic_id: str, mastery: float) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id})-[:HAS_PROGRESS]->(p:Progress)-[:FOR_TOPIC]->(t:Topic {id:$topic_id})
        SET p.mastery = $mastery, p.status = CASE WHEN $mastery >= 0.7 THEN 'mastered' ELSE 'in_progress' END
        RETURN p, t
        """
        return self.db.query(query, {"user_id": user_id, "topic_id": topic_id, "mastery": mastery})

    def mark_resource_complete(self, user_id: str, resource_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id})
        MATCH (r:Resource {id:$resource_id})
        MERGE (u)-[completed:COMPLETED_RESOURCE]->(r)
        SET completed.completed_at = $completed_at
        RETURN r, completed
        """
        import datetime
        return self.db.query(query, {"user_id": user_id, "resource_id": resource_id, "completed_at": datetime.datetime.now(datetime.UTC).isoformat()})

    def record_quiz_attempt(self, user_id: str, quiz_id: str, score: float) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {id:$user_id}), (q:Quiz {id:$quiz_id})
        CREATE (u)-[:TOOK]->(attempt:QuizAttempt {id:$attempt_id, score:$score, created_at:$created_at})-[:FOR_QUIZ]->(q)
        RETURN attempt, q
        """
        import datetime
        import uuid
        return self.db.query(query, {"user_id": user_id, "quiz_id": quiz_id, "score": score, "attempt_id": f"attempt_{uuid.uuid4().hex[:8]}", "created_at": datetime.datetime.now(datetime.UTC).isoformat()})

    def practice_questions(self, topic_id: str | None) -> list[dict[str, Any]]:
        query = """
        MATCH (t:Topic {id:$topic_id})-[:HAS_QUIZ]->(q:Quiz)
        RETURN t, q
        """
        return self.db.query(query, {"topic_id": topic_id}) if topic_id else []
