from datetime import date

from src.app.models.schemas import (
    BiomedicalRecord,
    Entity,
    EntityType,
    RelationType,
    TemporalRelation,
)


ENTITY_LEXICON: dict[str, Entity] = {
    "egfr": Entity(name="EGFR", entity_type=EntityType.GENE),
    "alk": Entity(name="ALK", entity_type=EntityType.GENE),
    "kras": Entity(name="KRAS", entity_type=EntityType.GENE),
    "non-small cell lung cancer": Entity(
        name="non-small cell lung cancer", entity_type=EntityType.DISEASE
    ),
    "lung cancer": Entity(name="non-small cell lung cancer", entity_type=EntityType.DISEASE),
    "osimertinib": Entity(name="osimertinib", entity_type=EntityType.DRUG),
    "crizotinib": Entity(name="crizotinib", entity_type=EntityType.DRUG),
    "sotorasib": Entity(name="sotorasib", entity_type=EntityType.DRUG),
    "t790m": Entity(name="T790M", entity_type=EntityType.BIOMARKER),
    "exon 20 insertion": Entity(name="exon 20 insertion", entity_type=EntityType.BIOMARKER),
    "mapk signaling": Entity(name="MAPK signaling", entity_type=EntityType.PATHWAY),
}

PREDICATE_TRIGGERS: list[tuple[str, RelationType]] = [
    ("predicts response to", RelationType.PREDICTS_RESPONSE),
    ("is resistant to", RelationType.RESISTANT_TO),
    ("associated with", RelationType.ASSOCIATED_WITH),
    ("treats", RelationType.TREATS),
    ("inhibits", RelationType.INHIBITS),
    ("part of", RelationType.PART_OF),
    ("activates", RelationType.PART_OF),
]


class RuleBasedBiomedicalExtractor:
    """Deterministic extraction for offline demos and tests."""

    def extract(self, record: BiomedicalRecord) -> list[TemporalRelation]:
        text = record.text
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        relations: list[TemporalRelation] = []

        for sentence in sentences:
            lowered = sentence.lower()
            entities = self._entities_in_text(lowered)
            for trigger, predicate in PREDICATE_TRIGGERS:
                if trigger not in lowered or len(entities) < 2:
                    continue
                subject, obj = self._choose_subject_object(lowered, trigger, entities)
                if subject and obj and subject.key != obj.key:
                    relations.append(
                        TemporalRelation(
                            subject=subject,
                            predicate=predicate,
                            object=obj,
                            observed_at=record.observed_at,
                            source_id=record.record_id,
                            evidence=f"{sentence}.",
                            confidence=0.9,
                        )
                    )
        return self._dedupe(relations)

    def _entities_in_text(self, lowered: str) -> list[Entity]:
        found = [(lowered.index(term), entity) for term, entity in ENTITY_LEXICON.items() if term in lowered]
        return [entity for _, entity in sorted(found, key=lambda item: item[0])]

    def _choose_subject_object(
        self, lowered: str, trigger: str, entities: list[Entity]
    ) -> tuple[Entity | None, Entity | None]:
        trigger_index = lowered.index(trigger)
        before = [entity for entity in entities if lowered.find(entity.name.lower()) < trigger_index]
        after = [entity for entity in entities if lowered.find(entity.name.lower()) > trigger_index]
        if before and after:
            return before[-1], after[0]
        if len(entities) >= 2:
            return entities[0], entities[1]
        return None, None

    def _dedupe(self, relations: list[TemporalRelation]) -> list[TemporalRelation]:
        seen: set[tuple[str, str, str, date, str]] = set()
        unique: list[TemporalRelation] = []
        for relation in relations:
            key = (
                relation.subject.key,
                relation.predicate.value,
                relation.object.key,
                relation.observed_at,
                relation.source_id,
            )
            if key not in seen:
                seen.add(key)
                unique.append(relation)
        return unique
