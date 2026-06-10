from src.app.agent.memory_agent import BiomedicalKGMemoryAgent
from src.app.graph.local_store import LocalTemporalGraphStore
from src.app.utils.config import Settings


def test_evaluation_report_has_bounded_scores():
    agent = BiomedicalKGMemoryAgent(LocalTemporalGraphStore(), Settings())

    report = agent.evaluate()

    assert report.records_evaluated == 4
    assert 0.0 <= report.relation_precision <= 1.0
    assert 0.0 <= report.relation_recall <= 1.0
    assert report.graph_consistency == 1.0
