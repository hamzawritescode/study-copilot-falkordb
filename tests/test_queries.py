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
