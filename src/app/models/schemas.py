from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    GENE = "gene"
    DISEASE = "disease"
    DRUG = "drug"
    BIOMARKER = "biomarker"
    PATHWAY = "pathway"


class RelationType(StrEnum):
    TREATS = "TREATS"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    INHIBITS = "INHIBITS"
    RESISTANT_TO = "RESISTANT_TO"
    PREDICTS_RESPONSE = "PREDICTS_RESPONSE"
    PART_OF = "PART_OF"


class Entity(BaseModel):
    name: str
    entity_type: EntityType

    @property
    def key(self) -> str:
        return f"{self.entity_type.value}:{self.name.lower()}"


class TemporalRelation(BaseModel):
    subject: Entity
    predicate: RelationType
    object: Entity
    observed_at: date
    source_id: str
    evidence: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BiomedicalRecord(BaseModel):
    record_id: str
    text: str
    observed_at: date
    expected_relations: list[TemporalRelation] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    as_of: date | None = None


class QueryEvidence(BaseModel):
    subject: str
    predicate: str
    object: str
    observed_at: date
    source_id: str
    evidence: str
    confidence: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    evidence: list[QueryEvidence]
    reasoning_path: list[str]


class IngestRequest(BaseModel):
    records: list[BiomedicalRecord] | None = None
    use_synthetic: bool = True


class IngestResponse(BaseModel):
    records_ingested: int
    relations_ingested: int
    backend: str


class GraphSummary(BaseModel):
    backend: str
    entity_count: int
    relation_count: int
    entity_types: dict[str, int]


class EvaluationReport(BaseModel):
    relation_precision: float
    relation_recall: float
    relation_f1: float
    temporal_order_accuracy: float
    graph_consistency: float
    records_evaluated: int
