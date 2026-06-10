from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.agent.memory_agent import BiomedicalKGMemoryAgent
from src.app.data.synthetic import load_synthetic_records
from src.app.graph.factory import build_graph_store
from src.app.models.schemas import (
    EvaluationReport,
    GraphSummary,
    IngestRequest,
    IngestResponse,
    QueryEvidence,
    QueryRequest,
    QueryResponse,
)
from src.app.utils.config import get_settings
from src.app.utils.logging import logger

settings = get_settings()
graph_store = build_graph_store(settings)
agent = BiomedicalKGMemoryAgent(graph_store=graph_store, settings=settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Biomedical KG Memory Agent with backend=%s", agent.backend_name)
    if settings.graph_backend.lower() == "local":
        agent.reset_and_seed()
    yield
    if hasattr(graph_store, "close"):
        graph_store.close()


app = FastAPI(
    title="Biomedical Temporal KG Memory Agent",
    version="1.0.0",
    description="Local-first biomedical memory agent using temporal graph facts and Neo4j Community.",
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "biomed-kg-memory-agent",
        "backend": agent.backend_name,
        "openai_required": False,
    }


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest):
    records = payload.records or []
    if payload.use_synthetic:
        records.extend(load_synthetic_records())
    return agent.ingest_records(records)


@app.post("/v1/query", response_model=QueryResponse)
def query_memory(payload: QueryRequest):
    return agent.answer(payload.question, top_k=payload.top_k, as_of=payload.as_of)


@app.get("/v1/timeline/{entity_name}", response_model=list[QueryEvidence])
def entity_timeline(entity_name: str):
    return agent.timeline(entity_name)


@app.get("/v1/graph/summary", response_model=GraphSummary)
def graph_summary():
    return GraphSummary(**agent.summary())


@app.get("/v1/evaluate", response_model=EvaluationReport)
def evaluate_default_dataset():
    return agent.evaluate()
