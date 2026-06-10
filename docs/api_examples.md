# API Examples

## Query

```bash
curl -X POST http://localhost:8000/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Which biomarker predicts response to osimertinib?\",\"top_k\":3}"
```

## Timeline

```bash
curl http://localhost:8000/v1/timeline/EGFR
```

## Graph Summary

```bash
curl http://localhost:8000/v1/graph/summary
```

## Evaluation

```bash
curl http://localhost:8000/v1/evaluate
```
