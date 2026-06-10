from src.app.graph.local_store import LocalTemporalGraphStore
from src.app.graph.neo4j_store import Neo4jTemporalGraphStore
from src.app.utils.config import Settings


def build_graph_store(settings: Settings):
    if settings.graph_backend.lower() == "neo4j":
        return Neo4jTemporalGraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
    return LocalTemporalGraphStore()
