from app.graph_schema import SCHEMA_QUERIES, SEED_QUERY


def test_schema_indexes_are_idempotent():
    assert len(SCHEMA_QUERIES) == 4
    assert all("CREATE INDEX IF NOT EXISTS" in query for query in SCHEMA_QUERIES)


def test_seed_contains_connected_learning_entities():
    for label in ("User", "Topic", "Progress", "SkillGap", "Resource", "Quiz"):
        assert f":{label}" in SEED_QUERY
    assert "PREREQUISITE_OF" in SEED_QUERY
    assert "HAS_RESOURCE" in SEED_QUERY
    assert "HAS_QUIZ" in SEED_QUERY
