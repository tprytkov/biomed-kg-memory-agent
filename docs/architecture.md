# Architecture Notes

The agent stores biomedical memory as dated graph facts:

```text
(Entity)-[:FACT {predicate, observed_at, source_id, evidence, confidence}]->(Entity)
```

Neo4j Community Edition is the production-like local backend. The NetworkX backend implements the same project-level behavior for fast tests and demos. This keeps the repository easy to evaluate while still demonstrating graph-database integration.

The extraction layer is intentionally deterministic by default. That makes CI behavior stable and avoids hidden API keys. Hugging Face local mode only reranks relation confidence and loads lazily.
