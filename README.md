# Biomedical Temporal KG Memory Agent

A local-first biomedical knowledge-graph memory agent for temporal clinical and scientific facts. The project extracts structured graph facts from synthetic biomedical notes, stores them in Neo4j Community Edition or an in-memory NetworkX backend, answers graph-grounded questions, and reports extraction/evaluation metrics.

No OpenAI API, paid hosted vector database, or cloud service is required. Rule-based extraction is the default so the project runs on a normal Windows Anaconda setup. Optional Hugging Face local mode is available when you want local embedding-based confidence reranking.

## Live Demo: Streamlit Public Frontend

Explore the [live Streamlit demo](https://biomed-kg-memory-agent-jqqguacema26da5fdfnk9m.streamlit.app/).

The public demo runs in self-contained mode using synthetic biomedical data. It does not
require FastAPI, Neo4j, Docker, an OpenAI API, or secrets.

## Project Summary

This repository demonstrates a recruiter-friendly backend project for biomedical AI infrastructure:

- FastAPI service for ingestion, temporal graph search, entity timelines, and evaluation.
- Neo4j Community Edition graph persistence through Docker Compose.
- Local in-memory graph backend for tests and demos when Neo4j is not running.
- Deterministic biomedical relation extraction by default.
- Optional local Hugging Face mode using `sentence-transformers`.
- Synthetic biomedical dataset covering genes, drugs, biomarkers, diseases, pathways, and dated evidence.
- Pytest coverage for extraction, graph memory, API behavior, and metrics.

## Architecture

```text
Synthetic biomedical records
        |
        v
Rule extractor / optional local HF reranker
        |
        v
TemporalRelation facts
        |
        +--> Neo4j Community graph backend
        |
        +--> Local NetworkX graph backend
        |
        v
FastAPI memory agent endpoints
        |
        v
Grounded answers, timelines, graph summary, metrics
```

## Local Setup on Windows Anaconda Prompt

Clone the repository and enter the project directory:

```bash
git clone https://github.com/tprytkov/biomed-kg-memory-agent.git
cd biomed-kg-memory-agent
```

Recommended one-command conda setup:

```bash
conda env create -f environment.yml
conda activate kgmemory
```

Manual setup using `requirements.txt`:

```bash
conda create -n kgmemory python=3.11 -y
conda activate kgmemory

pip install -r requirements.txt
```

The default backend is `GRAPH_BACKEND=local`, so you can run immediately without Docker:

```bash
uvicorn src.app.api.main:app --reload
```

Open:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Healthcheck: [http://localhost:8000/](http://localhost:8000/)

## Streamlit Portfolio Demo

Run the polished self-contained frontend directly from the project root:

```bash
streamlit run frontend/streamlit_app.py
```

The default mode runs the synthetic biomedical graph and memory agent directly in the
Streamlit process. It does not require FastAPI, Neo4j, Docker, an OpenAI API key, or a
Hugging Face model download.

To use the optional FastAPI mode, start the backend on the frontend's default API port:

```bash
python -m uvicorn src.app.api.main:app --reload --port 8001
```

Then select **FastAPI backend mode** in the Streamlit sidebar.

## Run With Neo4j Community Edition

Start the full local stack:

```bash
docker-compose up --build
```

Open:

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Neo4j Browser: [http://localhost:7474](http://localhost:7474)

Neo4j login:

```text
Username: neo4j
Password: biomed-memory
```

Seed the graph manually when running against Neo4j from Anaconda:

```bash
set GRAPH_BACKEND=neo4j
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=biomed-memory
python scripts\seed_graph.py
```

## API Examples

Ask a graph-grounded question:

```bash
curl -X POST http://localhost:8000/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What treats lung cancer with EGFR?\",\"top_k\":3}"
```

Get an entity timeline:

```bash
curl http://localhost:8000/v1/timeline/osimertinib
```

Inspect graph size:

```bash
curl http://localhost:8000/v1/graph/summary
```

Run evaluation:

```bash
curl http://localhost:8000/v1/evaluate
```

## Optional Hugging Face Local Mode

Rule extraction is the default and does not download models. To add local embedding-based confidence reranking, cache or install a SentenceTransformer model, then set:

```bash
set EXTRACTION_MODE=hf_local
set HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

This mode still does not use OpenAI or paid services. If the model is not cached, Hugging Face may download it during first use.

## Testing

From Anaconda Prompt with the `kgmemory` environment activated:

```bash
conda activate kgmemory
pytest -v
```

The tests use the local NetworkX graph backend so they do not require Docker or Neo4j.

## Evaluation Metrics

- `relation_precision`: fraction of extracted relation signatures that match expected synthetic labels.
- `relation_recall`: fraction of expected relation signatures recovered by the extractor.
- `relation_f1`: harmonic mean of precision and recall.
- `temporal_order_accuracy`: whether extracted facts retain the expected observation dates.
- `graph_consistency`: duplicate and self-loop sanity score for extracted graph facts.

## Repository Layout

```text
src/app/api/          FastAPI application
src/app/agent/        Memory-agent orchestration
src/app/data/         Synthetic biomedical records
src/app/extraction/   Rule-based and optional local HF extraction helpers
src/app/graph/        Neo4j and NetworkX graph stores
src/app/evals/        Evaluation metrics
frontend/             Streamlit portfolio demo
tests/                Pytest suite
scripts/              Local server and graph seeding helpers
docs/                 Architecture and API notes
```

## Why This Project Matters

Biomedical AI systems often need memory that is structured, dated, explainable, and auditable. This project shows how a local agent can preserve source evidence and observation time while supporting graph queries over diseases, biomarkers, genes, drugs, and pathways.
