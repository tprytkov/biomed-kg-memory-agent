from src.app.models.schemas import TemporalRelation


class LocalHuggingFaceRelationRanker:
    """Optional local-only confidence reranker.

    The model loads lazily so the default rule mode stays lightweight and network-free.
    Use cached models or pre-download them with Hugging Face tooling for fully offline runs.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def rank(self, relations: list[TemporalRelation], query: str | None = None) -> list[TemporalRelation]:
        if not relations:
            return []
        model = self._load()
        reference = query or "biomedical temporal relation"
        texts = [
            f"{r.subject.name} {r.predicate.value} {r.object.name}. {r.evidence}" for r in relations
        ]
        embeddings = model.encode([reference, *texts], normalize_embeddings=True)
        query_vec = embeddings[0]
        scored = []
        for relation, vector in zip(relations, embeddings[1:], strict=True):
            relation.confidence = float(max(0.0, min(1.0, (query_vec @ vector + 1.0) / 2.0)))
            scored.append(relation)
        return sorted(scored, key=lambda relation: relation.confidence, reverse=True)
