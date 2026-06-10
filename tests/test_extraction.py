from src.app.data.synthetic import load_synthetic_records
from src.app.extraction.rules import RuleBasedBiomedicalExtractor


def test_rule_extractor_finds_temporal_relations():
    records = load_synthetic_records()
    extractor = RuleBasedBiomedicalExtractor()

    relations = extractor.extract(records[0])

    assert len(relations) == 2
    assert relations[0].observed_at == records[0].observed_at
    assert {relation.predicate.value for relation in relations} >= {
        "ASSOCIATED_WITH",
        "PREDICTS_RESPONSE",
    }
