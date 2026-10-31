from app.repository import StudyRepository


def test_next_topics_query_contains_prerequisite_guard():
    class FakeDb:
        def query(self, query, params):
            assert "PREREQUISITE_OF" in query
            assert "mastery >= 0.7" in query
            return []

    StudyRepository(FakeDb()).next_topics("u_001")


def test_progress_query_is_parameterized():
    class FakeDb:
        def query(self, query, params):
            assert "$mastery" in query
            assert params["topic_id"] == "t_data"
            return []

    StudyRepository(FakeDb()).record_progress("u_001", "t_data", 0.75)


def test_blocked_topics_query_exposes_unmet_prerequisite():
    class FakeDb:
        def query(self, query, params):
            assert "mp.mastery < 0.7" in query
            assert "PREREQUISITE_OF" in query
            assert params["minutes"] == 30
            return []

    StudyRepository(FakeDb()).blocked_topics("u_001", 30)
