from datetime import date

from src.app.models.schemas import (
    BiomedicalRecord,
    Entity,
    EntityType,
    RelationType,
    TemporalRelation,
)


def e(name: str, entity_type: EntityType) -> Entity:
    return Entity(name=name, entity_type=entity_type)


def rel(
    subject: Entity,
    predicate: RelationType,
    obj: Entity,
    observed_at: date,
    source_id: str,
    evidence: str,
    confidence: float = 0.95,
) -> TemporalRelation:
    return TemporalRelation(
        subject=subject,
        predicate=predicate,
        object=obj,
        observed_at=observed_at,
        source_id=source_id,
        evidence=evidence,
        confidence=confidence,
    )


def load_synthetic_records() -> list[BiomedicalRecord]:
    egfr = e("EGFR", EntityType.GENE)
    alk = e("ALK", EntityType.GENE)
    kras = e("KRAS", EntityType.GENE)
    nsclc = e("non-small cell lung cancer", EntityType.DISEASE)
    osimertinib = e("osimertinib", EntityType.DRUG)
    crizotinib = e("crizotinib", EntityType.DRUG)
    sotorasib = e("sotorasib", EntityType.DRUG)
    t790m = e("T790M", EntityType.BIOMARKER)
    exon20 = e("exon 20 insertion", EntityType.BIOMARKER)
    mapk = e("MAPK signaling", EntityType.PATHWAY)

    rows = [
        (
            "SYN-001",
            date(2020, 4, 15),
            "EGFR is associated with non-small cell lung cancer. "
            "The T790M biomarker predicts response to osimertinib.",
            [
                rel(egfr, RelationType.ASSOCIATED_WITH, nsclc, date(2020, 4, 15), "SYN-001", "EGFR is associated with non-small cell lung cancer."),
                rel(t790m, RelationType.PREDICTS_RESPONSE, osimertinib, date(2020, 4, 15), "SYN-001", "The T790M biomarker predicts response to osimertinib."),
            ],
        ),
        (
            "SYN-002",
            date(2021, 7, 2),
            "Osimertinib treats non-small cell lung cancer with EGFR mutations. "
            "Exon 20 insertion is resistant to osimertinib in this cohort.",
            [
                rel(osimertinib, RelationType.TREATS, nsclc, date(2021, 7, 2), "SYN-002", "Osimertinib treats non-small cell lung cancer with EGFR mutations."),
                rel(exon20, RelationType.RESISTANT_TO, osimertinib, date(2021, 7, 2), "SYN-002", "Exon 20 insertion is resistant to osimertinib in this cohort."),
            ],
        ),
        (
            "SYN-003",
            date(2022, 2, 11),
            "ALK rearrangement is associated with non-small cell lung cancer. "
            "Crizotinib inhibits ALK signaling and treats ALK-positive disease.",
            [
                rel(alk, RelationType.ASSOCIATED_WITH, nsclc, date(2022, 2, 11), "SYN-003", "ALK rearrangement is associated with non-small cell lung cancer."),
                rel(crizotinib, RelationType.INHIBITS, alk, date(2022, 2, 11), "SYN-003", "Crizotinib inhibits ALK signaling."),
                rel(crizotinib, RelationType.TREATS, nsclc, date(2022, 2, 11), "SYN-003", "Crizotinib treats ALK-positive disease."),
            ],
        ),
        (
            "SYN-004",
            date(2023, 9, 5),
            "KRAS G12C activates MAPK signaling in lung cancer. "
            "Sotorasib inhibits KRAS and treats KRAS G12C non-small cell lung cancer.",
            [
                rel(kras, RelationType.PART_OF, mapk, date(2023, 9, 5), "SYN-004", "KRAS G12C activates MAPK signaling in lung cancer."),
                rel(sotorasib, RelationType.INHIBITS, kras, date(2023, 9, 5), "SYN-004", "Sotorasib inhibits KRAS."),
                rel(sotorasib, RelationType.TREATS, nsclc, date(2023, 9, 5), "SYN-004", "Sotorasib treats KRAS G12C non-small cell lung cancer."),
            ],
        ),
    ]
    return [
        BiomedicalRecord(
            record_id=record_id,
            observed_at=observed_at,
            text=text,
            expected_relations=expected,
        )
        for record_id, observed_at, text, expected in rows
    ]
