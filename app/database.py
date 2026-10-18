import logging
from typing import Any

from falkordb import FalkorDB
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import Settings

logger = logging.getLogger(__name__)


class GraphDatabase:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: FalkorDB | None = None
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._client = FalkorDB(
                host=self.settings.falkordb_host,
                port=self.settings.falkordb_port,
                username=self.settings.falkordb_username,
                password=self.settings.falkordb_password,
            )
            self._graph = self._client.select_graph(self.settings.falkordb_graph)
        return self._graph

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5), reraise=True)
    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self.graph.query(cypher, params or {})
        headers = list(result.header) if result.header else []
        return [dict(zip(headers, row)) for row in result.result_set]

    def health(self) -> bool:
        try:
            self.query("RETURN 1 AS ok")
            return True
        except Exception:
            logger.exception("FalkorDB health check failed")
            return False
