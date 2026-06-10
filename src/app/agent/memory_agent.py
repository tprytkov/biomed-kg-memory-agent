import re
from datetime import date

from src.app.data.synthetic import load_synthetic_records
from src.app.extraction.hf_local import LocalHuggingFaceRelationRanker
from src.app.extraction.rules import RuleBasedBiomedicalExtractor
from src.app.models.schemas import (
    BiomedicalRecord,
    EvaluationReport,
    IngestResponse,
    QueryResponse,
    TemporalRelation,
)
from src.app.utils.config import Settings


class BiomedicalKGMemoryAgent:
    def __init__(self, graph_store, settings: Settings):
        self.graph_store = graph_store
        self.settings = settings
        self.extractor = RuleBasedBiomedicalExtractor()
        self.ranker = (
            LocalHuggingFaceRelationRanker(settings.hf_model_name)
            if settings.extraction_mode.lower() == "hf_local"
            else None
        )

    @property
    def backend_name(self) -> str:
        return self.graph_store.backend_name

    def reset_and_seed(self) -> IngestResponse:
        self.graph_store.clear()
        return self.ingest_records(load_synthetic_records())

    def ingest_records(self, records: list[BiomedicalRecord]) -> IngestResponse:
        extracted: list[TemporalRelation] = []
        for record in records:
            relations = self.extractor.extract(record)
            if self.ranker:
                relations = self.ranker.rank(relations)
            extracted.extend(relations)
        count = self.graph_store.upsert_relations(extracted)
        return IngestResponse(
            records_ingested=len(records),
            relations_ingested=count,
            backend=self.backend_name,
        )

    def answer(self, question: str, top_k: int = 5, as_of: date | None = None) -> QueryResponse:
        terms = self._query_terms(question)
        evidence = self.graph_store.query_relations(terms=terms, top_k=top_k, as_of=as_of)
        if not evidence:
            return QueryResponse(
                question=question,
                answer="No matching temporal biomedical graph facts were found.",
                evidence=[],
                reasoning_path=[],
            )
        answer = self._synthesize_answer(question, evidence, as_of)
        path = [f"{item.subject} -[{item.predicate}]-> {item.object}" for item in evidence]
        return QueryResponse(question=question, answer=answer, evidence=evidence, reasoning_path=path)

    def timeline(self, entity_name: str):
        return self.graph_store.timeline(entity_name)

    def summary(self):
        return self.graph_store.summary()

    def evaluate(self, records: list[BiomedicalRecord] | None = None) -> EvaluationReport:
        from src.app.evals.metrics import evaluate_extraction

        return evaluate_extraction(records or load_synthetic_records(), self.extractor)

    def _query_terms(self, question: str) -> list[str]:
        cleaned = re.sub(r"[^A-Za-z0-9\s-]", " ", question).lower()
        stopwords = {
            "what",
            "which",
            "does",
            "with",
            "about",
            "show",
            "the",
            "and",
            "for",
            "are",
            "was",
            "were",
            "is",
            "to",
            "in",
            "of",
            "as",
        }
        terms = [token for token in cleaned.split() if len(token) > 2 and token not in stopwords]
        biomedical_phrases = [
            "non-small cell lung cancer",
            "lung cancer",
            "exon 20 insertion",
            "mapk signaling",
        ]
        return [phrase for phrase in biomedical_phrases if phrase in cleaned] + terms

    def _synthesize_answer(self, question: str, evidence, as_of: date | None) -> str:
        temporal_clause = f" as of {as_of.isoformat()}" if as_of else ""
        first = evidence[0]
        if len(evidence) == 1:
            return (
                f"Based on graph memory{temporal_clause}, {first.subject} "
                f"{first.predicate.lower().replace('_', ' ')} {first.object} "
                f"({first.observed_at.isoformat()}, {first.source_id})."
            )
        facts = "; ".join(
            f"{item.subject} {item.predicate.lower().replace('_', ' ')} {item.object}"
            for item in evidence[:3]
        )
        return f"Based on graph memory{temporal_clause}, the strongest linked facts are: {facts}."
