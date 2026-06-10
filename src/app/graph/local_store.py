from collections import Counter
from datetime import date

import networkx as nx

from src.app.models.schemas import Entity, QueryEvidence, TemporalRelation


class LocalTemporalGraphStore:
    backend_name = "local"

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def clear(self) -> None:
        self.graph.clear()

    def upsert_relations(self, relations: list[TemporalRelation]) -> int:
        for relation in relations:
            self._upsert_entity(relation.subject)
            self._upsert_entity(relation.object)
            key = f"{relation.source_id}:{relation.predicate.value}:{relation.observed_at.isoformat()}"
            self.graph.add_edge(
                relation.subject.key,
                relation.object.key,
                key=key,
                predicate=relation.predicate.value,
                observed_at=relation.observed_at,
                source_id=relation.source_id,
                evidence=relation.evidence,
                confidence=relation.confidence,
            )
        return len(relations)

    def query_relations(
        self, terms: list[str], top_k: int = 5, as_of: date | None = None
    ) -> list[QueryEvidence]:
        term_set = {term.lower() for term in terms if term}
        scored: list[tuple[int, QueryEvidence]] = []
        for source, target, data in self.graph.edges(data=True):
            observed_at = data["observed_at"]
            if as_of and observed_at > as_of:
                continue
            source_data = self.graph.nodes[source]
            target_data = self.graph.nodes[target]
            haystack = " ".join(
                [
                    source_data["name"],
                    source_data["entity_type"],
                    target_data["name"],
                    target_data["entity_type"],
                    data["predicate"],
                    data["evidence"],
                ]
            ).lower()
            score = sum(1 for term in term_set if term in haystack)
            if score:
                scored.append(
                    (
                        score,
                        QueryEvidence(
                            subject=source_data["name"],
                            predicate=data["predicate"],
                            object=target_data["name"],
                            observed_at=observed_at,
                            source_id=data["source_id"],
                            evidence=data["evidence"],
                            confidence=data["confidence"],
                        ),
                    )
                )
        scored.sort(key=lambda item: (item[0], item[1].observed_at, item[1].confidence), reverse=True)
        return [evidence for _, evidence in scored[:top_k]]

    def timeline(self, entity_name: str) -> list[QueryEvidence]:
        target_name = entity_name.lower()
        events: list[QueryEvidence] = []
        for source, target, data in self.graph.edges(data=True):
            source_data = self.graph.nodes[source]
            target_data = self.graph.nodes[target]
            if target_name not in {source_data["name"].lower(), target_data["name"].lower()}:
                continue
            events.append(
                QueryEvidence(
                    subject=source_data["name"],
                    predicate=data["predicate"],
                    object=target_data["name"],
                    observed_at=data["observed_at"],
                    source_id=data["source_id"],
                    evidence=data["evidence"],
                    confidence=data["confidence"],
                )
            )
        return sorted(events, key=lambda event: event.observed_at)

    def summary(self) -> dict:
        type_counts = Counter(data["entity_type"] for _, data in self.graph.nodes(data=True))
        return {
            "backend": self.backend_name,
            "entity_count": self.graph.number_of_nodes(),
            "relation_count": self.graph.number_of_edges(),
            "entity_types": dict(type_counts),
        }

    def _upsert_entity(self, entity: Entity) -> None:
        self.graph.add_node(entity.key, name=entity.name, entity_type=entity.entity_type.value)
