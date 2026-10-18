import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import GraphDatabase
from app.graph_schema import SCHEMA_QUERIES, SEED_QUERY


def main() -> None:
    database = GraphDatabase(get_settings())
    for query in SCHEMA_QUERIES:
        database.query(query)
    database.query("MATCH (n) DETACH DELETE n")
    database.query(SEED_QUERY)
    print("Study Copilot graph seeded")


if __name__ == "__main__":
    main()
