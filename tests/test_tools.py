import pytest

from app.tools import ActionService


class FakeRepository:
    def record_progress(self, user_id, topic_id, mastery):
        return [{"topic_id": topic_id, "mastery": mastery}]

    def mark_resource_complete(self, user_id, resource_id):
        return [{"resource_id": resource_id}]


def test_confirm_executes_validated_progress_action():
    service = ActionService(FakeRepository())
    action = service.stage(
        "u_001",
        "update_progress",
        {"topic_id": "t_data", "mastery": 0.75},
        "Update progress",
    )

    result = service.confirm(action.action_id, approved=True)

    assert result["status"] == "executed"
    assert result["result"]["message"] == "Progress updated"


def test_stage_rejects_invalid_mastery():
    service = ActionService(FakeRepository())

    with pytest.raises(ValueError, match="Mastery must be between 0 and 1"):
        service.stage(
            "u_001",
            "update_progress",
            {"topic_id": "t_data", "mastery": 1.5},
            "Invalid progress",
        )


def test_confirm_rejects_missing_action():
    service = ActionService(FakeRepository())

    with pytest.raises(KeyError, match="Action no longer exists"):
        service.confirm("act_missing", approved=True)
