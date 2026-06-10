from src.app.models.schemas import BiomedicalRecord, EvaluationReport, TemporalRelation


def relation_signature(relation: TemporalRelation) -> tuple[str, str, str]:
    return (
        relation.subject.key,
        relation.predicate.value,
        relation.object.key,
    )


def dated_signature(relation: TemporalRelation) -> tuple[str, str, str, str]:
    subject, predicate, obj = relation_signature(relation)
    return subject, predicate, obj, relation.observed_at.isoformat()


def precision_recall_f1(predicted: set[tuple], expected: set[tuple]) -> tuple[float, float, float]:
    if not predicted and not expected:
        return 1.0, 1.0, 1.0
    true_positive = len(predicted & expected)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def temporal_order_accuracy(predicted: list[TemporalRelation], expected: list[TemporalRelation]) -> float:
    expected_dates = {relation_signature(relation): relation.observed_at for relation in expected}
    comparable = [
        relation
        for relation in predicted
        if relation_signature(relation) in expected_dates
    ]
    if not comparable:
        return 0.0 if expected else 1.0
    correct = sum(
        1
        for relation in comparable
        if relation.observed_at == expected_dates[relation_signature(relation)]
    )
    return correct / len(comparable)


def graph_consistency_score(predicted: list[TemporalRelation]) -> float:
    if not predicted:
        return 1.0
    invalid = 0
    seen: set[tuple[str, str, str, str, str]] = set()
    for relation in predicted:
        key = (
            relation.subject.key,
            relation.predicate.value,
            relation.object.key,
            relation.observed_at.isoformat(),
            relation.source_id,
        )
        if relation.subject.key == relation.object.key or key in seen:
            invalid += 1
        seen.add(key)
    return max(0.0, 1.0 - invalid / len(predicted))


def evaluate_extraction(records: list[BiomedicalRecord], extractor) -> EvaluationReport:
    predicted: list[TemporalRelation] = []
    expected: list[TemporalRelation] = []
    for record in records:
        predicted.extend(extractor.extract(record))
        expected.extend(record.expected_relations)

    precision, recall, f1 = precision_recall_f1(
        {relation_signature(relation) for relation in predicted},
        {relation_signature(relation) for relation in expected},
    )
    return EvaluationReport(
        relation_precision=round(precision, 4),
        relation_recall=round(recall, 4),
        relation_f1=round(f1, 4),
        temporal_order_accuracy=round(temporal_order_accuracy(predicted, expected), 4),
        graph_consistency=round(graph_consistency_score(predicted), 4),
        records_evaluated=len(records),
    )
