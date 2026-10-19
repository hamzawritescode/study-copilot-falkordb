from fastapi.testclient import TestClient

from app.main import app, agent


class FakeAgent:
    def respond(self, user_id, message):
        return {"answer": "Use Data Structures next.", "context": [], "decision": None, "pending_action_id": None}


def test_chat_validates_and_returns_response(monkeypatch):
    monkeypatch.setattr("app.main.agent", FakeAgent())
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "What next?", "user_id": "u_001"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Use Data Structures next."


def test_chat_rejects_empty_message():
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "", "user_id": "u_001"})
    assert response.status_code == 422


def test_confirm_rejects_unknown_action():
    client = TestClient(app)
    response = client.post("/api/actions/act_missing/confirm", json={"approved": True})
    assert response.status_code == 404


def test_confirm_rejects_overlong_action_id():
    client = TestClient(app)
    action_id = "a" * 33
    response = client.post(f"/api/actions/{action_id}/confirm", json={"approved": True})
    assert response.status_code == 422
