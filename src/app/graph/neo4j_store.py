from collections import Counter
from datetime import date

from neo4j import GraphDatabase

from src.app.models.schemas import Entity, QueryEvidence, TemporalRelation


class Neo4jTemporalGraphStore:
    backend_name = "neo4j"

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def clear(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def upsert_relations(self, relations: list[TemporalRelation]) -> int:
        with self.driver.session() as session:
            for relation in relations:
                session.execute_write(self._merge_relation, relation)
        return len(relations)

    def query_relations(
        self, terms: list[str], top_k: int = 5, as_of: date | None = None
    ) -> list[QueryEvidence]:
        query = """
        MATCH (s:Entity)-[r:FACT]->(o:Entity)
        WHERE ($as_of IS NULL OR date(r.observed_at) <= date($as_of))
        WITH s, r, o,
             toLower(s.name + ' ' + s.entity_type + ' ' + o.name + ' ' + o.entity_type + ' ' +
                     r.predicate + ' ' + r.evidence) AS haystack
        WITH s, r, o,
             reduce(score = 0, term IN $terms |
                    score + CASE WHEN haystack CONTAINS toLower(term) THEN 1 ELSE 0 END) AS score
        WHERE score > 0
        RETURN s.name AS subject, r.predicate AS predicate, o.name AS object,
               r.observed_at AS observed_at, r.source_id AS source_id,
               r.evidence AS evidence, r.confidence AS confidence, score
        ORDER BY score DESC, r.observed_at DESC, r.confidence DESC
        LIMIT $top_k
        """
        with self.driver.session() as session:
            rows = session.run(
                query,
                terms=[term.lower() for term in terms],
                top_k=top_k,
                as_of=as_of.isoformat() if as_of else None,
            )
            return [self._row_to_evidence(row) for row in rows]

    def timeline(self, entity_name: str) -> list[QueryEvidence]:
        query = """
        MATCH (s:Entity)-[r:FACT]->(o:Entity)
        WHERE toLower(s.name) = toLower($entity_name) OR toLower(o.name) = toLower($entity_name)
        RETURN s.name AS subject, r.predicate AS predicate, o.name AS object,
               r.observed_at AS observed_at, r.source_id AS source_id,
               r.evidence AS evidence, r.confidence AS confidence
        ORDER BY r.observed_at ASC
        """
        with self.driver.session() as session:
            return [self._row_to_evidence(row) for row in session.run(query, entity_name=entity_name)]

    def summary(self) -> dict:
        with self.driver.session() as session:
            entity_rows = session.run("MATCH (n:Entity) RETURN n.entity_type AS type, count(n) AS count")
            relation_count = session.run("MATCH (:Entity)-[r:FACT]->(:Entity) RETURN count(r) AS count").single()
            type_counts = Counter()
            entity_total = 0
            for row in entity_rows:
                type_counts[row["type"]] = row["count"]
                entity_total += row["count"]
            return {
                "backend": self.backend_name,
                "entity_count": entity_total,
                "relation_count": relation_count["count"] if relation_count else 0,
                "entity_types": dict(type_counts),
            }

    @staticmethod
    def _merge_relation(tx, relation: TemporalRelation) -> None:
        tx.run(
            """
            MERGE (s:Entity {key: $subject_key})
            SET s.name = $subject_name, s.entity_type = $subject_type
            MERGE (o:Entity {key: $object_key})
            SET o.name = $object_name, o.entity_type = $object_type
            MERGE (s)-[r:FACT {
                source_id: $source_id,
                predicate: $predicate,
                observed_at: $observed_at
            }]->(o)
            SET r.evidence = $evidence, r.confidence = $confidence
            """,
            subject_key=relation.subject.key,
            subject_name=relation.subject.name,
            subject_type=relation.subject.entity_type.value,
            object_key=relation.object.key,
            object_name=relation.object.name,
            object_type=relation.object.entity_type.value,
            source_id=relation.source_id,
            predicate=relation.predicate.value,
            observed_at=relation.observed_at.isoformat(),
            evidence=relation.evidence,
            confidence=relation.confidence,
        )

    @staticmethod
    def _row_to_evidence(row) -> QueryEvidence:
        observed_at = row["observed_at"]
        if hasattr(observed_at, "to_native"):
            observed_at = observed_at.to_native()
        elif isinstance(observed_at, str):
            observed_at = date.fromisoformat(observed_at)
        return QueryEvidence(
            subject=row["subject"],
            predicate=row["predicate"],
            object=row["object"],
            observed_at=observed_at,
            source_id=row["source_id"],
            evidence=row["evidence"],
            confidence=float(row["confidence"]),
        )
