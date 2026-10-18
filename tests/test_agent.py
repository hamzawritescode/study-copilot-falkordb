from app.agent import StudyAgent
from app.schemas import ActionDecision


class FakeRepository:
    def user_context(self, user_id):
        return [{"t": {"id": "t_data", "name": "Data Structures"}}]

    def next_topics(self, user_id, available_minutes=45):
        return [{"candidate": {"id": "t_data", "name": "Data Structures"}, "resource": {"title": "Choosing the Right Collection"}}]


class FakeActions:
    def stage(self, user_id, name, parameters, reason):
        return type("Pending", (), {"action_id": "act_test"})()


def test_recommendation_is_grounded():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "What should I study next?")
    assert result["decision"].action == "recommend_next_topic"
    assert result["decision"].parameters["topic_id"] == "t_data"
    assert "Data Structures" in result["answer"]


def test_plan_requires_confirmation():
    agent = StudyAgent(FakeRepository(), FakeActions(), None)
    result = agent.respond("u_001", "Build me a study plan")
    assert result["decision"].requires_confirmation is True
    assert result["pending_action_id"] == "act_test"
