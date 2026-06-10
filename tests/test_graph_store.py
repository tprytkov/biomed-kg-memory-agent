from src.app.data.synthetic import load_synthetic_records
from src.app.extraction.rules import RuleBasedBiomedicalExtractor
from src.app.graph.local_store import LocalTemporalGraphStore


def test_local_graph_query_and_timeline():
    store = LocalTemporalGraphStore()
    extractor = RuleBasedBiomedicalExtractor()
    relations = []
    for record in load_synthetic_records():
        relations.extend(extractor.extract(record))

    inserted = store.upsert_relations(relations)
    results = store.query_relations(["osimertinib", "lung cancer"], top_k=3)
    timeline = store.timeline("osimertinib")

    assert inserted >= 7
    assert results
    assert timeline == sorted(timeline, key=lambda event: event.observed_at)
    assert store.summary()["entity_count"] >= 7
