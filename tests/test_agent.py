from app.agent import StudyAgent
from app.schemas import ActionDecision


class FakeRepository:
    def user_context(self, user_id):
        return [{"u": {"available_minutes": 45}, "t": {"id": "t_python", "name": "Python Functions"}, "p": {"mastery": 0.82}}]

    def next_topics(self, user_id, available_minutes=45):
        return [{"candidate": {"id": "t_data", "name": "Data Structures"}, "resource": {"id": "r_data", "title": "Choosing the Right Collection"}, "quiz": {"id": "q_data", "title": "Data Structures Checkpoint"}}]

    def blocked_topics(self, user_id, available_minutes=45):
        return [{"candidate": {"id": "t_recursion", "name": "Recursion"}, "prerequisite": {"id": "t_data", "name": "Data Structures"}, "mp": {"mastery": 0.42}}]

    def evidence_path(self, user_id, topic_id):
        return [{"nodes": [{"id": "t_python", "name": "Python Functions"}, {"id": topic_id, "name": "Data Structures"}], "relationships": ["PREREQUISITE_OF"]}]


class FakeActions:
    def stage(self, user_id, name, parameters, reason):
        return type("Pending", (), {"action_id": "act_test"})()


def test_recommendation_is_grounded():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "What should I study next?")
    assert result["decision"].action == "recommend_next_topic"
    assert result["decision"].parameters["topic_id"] == "t_data"
    assert "Data Structures" in result["answer"]
    assert result["evidence"]["recommended_topic"]["id"] == "t_data"
    assert result["evidence"]["available_time"] == 45
    assert result["blocked_candidates"][0]["topic"]["id"] == "t_recursion"
    assert "below the 0.70 threshold" in result["blocked_candidates"][0]["reason"]


def test_plan_without_topic_asks_for_clarification():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "Build me a study plan")
    assert result["decision"].requires_confirmation is False
    assert result["pending_action_id"] is None
    assert "Which topic" in result["answer"]


def test_plan_for_named_topic_requires_confirmation():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "Build a study plan for Data Structures")
    assert result["decision"].requires_confirmation is True
    assert result["decision"].parameters["topic_ids"] == ["t_data"]
    assert result["pending_action_id"] == "act_test"


def test_quiz_requires_name_and_score():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "Record a quiz attempt for q_data")
    assert result["decision"].requires_confirmation is False
    assert "score" in result["answer"]


def test_progress_parses_topic_and_mastery():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "Update progress for t_data to mastery 0.75")
    assert result["decision"].parameters["topic_id"] == "t_data"
    assert result["decision"].parameters["mastery"] == 0.75
