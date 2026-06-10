from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.agent.memory_agent import BiomedicalKGMemoryAgent
from src.app.data.synthetic import load_synthetic_records
from src.app.graph.local_store import LocalTemporalGraphStore
from src.app.utils.config import Settings


APP_TITLE = "Biomedical Temporal Knowledge-Graph Memory Agent"
DEMO_MODE = "Self-contained demo mode"
API_MODE = "FastAPI backend mode"
SAMPLE_QUESTIONS = [
    "What treats non-small cell lung cancer?",
    "What is associated with EGFR?",
    "Which biomarker predicts response to osimertinib?",
    "What inhibits KRAS?",
    "What was known about osimertinib by 2021?",
]

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px;}
        [data-testid="stSidebar"] {background-color: #f6f8fb;}
        .hero {
            padding: 1.4rem 1.6rem;
            border: 1px solid #dbe4ee;
            border-radius: 14px;
            background: linear-gradient(135deg, #f7fbff 0%, #eef7f5 100%);
            margin-bottom: 1.25rem;
        }
        .hero h1 {margin: 0 0 0.45rem 0; color: #12344d; font-size: 2.05rem;}
        .hero p {margin: 0; color: #456174; font-size: 1.02rem; max-width: 920px;}
        .status-card {
            border-left: 4px solid #168aad;
            background: #f4f9fb;
            padding: 0.7rem 0.9rem;
            border-radius: 6px;
            color: #294c60;
        }
        .small-label {font-size: 0.78rem; color: #607789; text-transform: uppercase;}
        div[data-testid="stMetric"] {
            border: 1px solid #e0e7ef;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            background-color: #ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def build_demo_agent() -> BiomedicalKGMemoryAgent:
    settings = Settings(graph_backend="local", extraction_mode="rule")
    agent = BiomedicalKGMemoryAgent(LocalTemporalGraphStore(), settings)
    agent.reset_and_seed()
    return agent


def api_request(
    api_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[Any | None, str | None]:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.request(method, f"{api_url.rstrip('/')}{path}", json=payload)
            response.raise_for_status()
            return response.json(), None
    except httpx.HTTPError as exc:
        return None, str(exc)


def model_rows(items: list[Any]) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        row = item.model_dump(mode="json") if hasattr(item, "model_dump") else dict(item)
        if "predicate" in row:
            row["predicate"] = row["predicate"].replace("_", " ").title()
        rows.append(row)
    return rows


def demo_relation_rows(agent: BiomedicalKGMemoryAgent) -> list[dict[str, Any]]:
    rows = []
    graph = agent.graph_store.graph
    for source, target, data in graph.edges(data=True):
        rows.append(
            {
                "subject": graph.nodes[source]["name"],
                "relation": data["predicate"].replace("_", " ").title(),
                "object": graph.nodes[target]["name"],
                "observed_at": data["observed_at"].isoformat(),
                "source": data["source_id"],
                "confidence": round(data["confidence"] * 100),
            }
        )
    return sorted(rows, key=lambda row: (row["observed_at"], row["subject"]))


def demo_entities(agent: BiomedicalKGMemoryAgent) -> list[str]:
    names = {data["name"] for _, data in agent.graph_store.graph.nodes(data=True)}
    return sorted(names, key=str.lower)


def show_metrics(summary: dict[str, Any]) -> None:
    columns = st.columns(4)
    columns[0].metric("Entities", summary.get("entity_count", 0))
    columns[1].metric("Temporal relations", summary.get("relation_count", 0))
    columns[2].metric("Entity types", len(summary.get("entity_types", {})))
    columns[3].metric("Graph backend", str(summary.get("backend", "unknown")).title())


st.markdown(
    f"""
    <div class="hero">
        <h1>{APP_TITLE}</h1>
        <p>
            A local-first portfolio demo that extracts dated biomedical facts, stores them as
            an explainable graph, and answers questions with source-grounded temporal evidence.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Demo controls")
    mode = st.radio("Application mode", [DEMO_MODE, API_MODE])
    st.caption(
        "Demo mode runs entirely in this Streamlit process using synthetic data, "
        "NetworkX, and deterministic rules."
    )

    api_url = "http://127.0.0.1:8001"
    api_health = None
    if mode == API_MODE:
        api_url = st.text_input("FastAPI URL", value=api_url)
        if st.button("Check API connection", width="stretch"):
            api_health, api_error = api_request(api_url, "GET", "/")
            if api_error:
                st.error("Backend unavailable. Start FastAPI or switch to demo mode.")
            else:
                st.success(f"Connected to {api_health.get('backend', 'unknown')} backend")

    st.divider()
    st.markdown("**Runtime guarantees in demo mode**")
    st.caption("No OpenAI API · No Neo4j · No Docker · No model download")
    st.divider()
    st.caption("Synthetic data only. Not intended for clinical decision-making.")

agent = build_demo_agent() if mode == DEMO_MODE else None
tabs = st.tabs(
    [
        "Graph overview",
        "Ask memory agent",
        "Entity timeline",
        "Evaluation",
        "Technical details",
    ]
)

with tabs[0]:
    st.header("Graph overview")
    st.write("Inspect the entities and dated relationships currently available to graph memory.")

    if mode == DEMO_MODE:
        summary = agent.summary()
        show_metrics(summary)

        left, right = st.columns([1, 2])
        with left:
            st.subheader("Entity distribution")
            entity_type_rows = [
                {"entity_type": entity_type.title(), "count": count}
                for entity_type, count in sorted(summary["entity_types"].items())
            ]
            st.dataframe(entity_type_rows, width="stretch", hide_index=True)
        with right:
            st.subheader("Entity catalog")
            entity_rows = [
                {
                    "entity": data["name"],
                    "type": data["entity_type"].title(),
                }
                for _, data in agent.graph_store.graph.nodes(data=True)
            ]
            st.dataframe(
                sorted(entity_rows, key=lambda row: (row["type"], row["entity"].lower())),
                width="stretch",
                hide_index=True,
            )

        st.subheader("Temporal relation memory")
        st.dataframe(
            demo_relation_rows(agent),
            width="stretch",
            hide_index=True,
            column_config={
                "confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0, max_value=100, format="%d%%"
                )
            },
        )
    else:
        summary, error = api_request(api_url, "GET", "/v1/graph/summary")
        if error:
            st.warning("Connect to the FastAPI backend to load graph metrics.")
            st.code(
                "python -m uvicorn src.app.api.main:app --reload --port 8001",
                language="powershell",
            )
        else:
            show_metrics(summary)
            st.subheader("Entity distribution")
            st.dataframe(
                [
                    {"entity_type": key.title(), "count": value}
                    for key, value in sorted(summary["entity_types"].items())
                ],
                width="stretch",
                hide_index=True,
            )
            st.info(
                "The current API exposes aggregate graph statistics. "
                "Detailed relation inspection remains available in self-contained demo mode."
            )

with tabs[1]:
    st.header("Ask the memory agent")
    st.write("Submit a biomedical question and review the exact graph evidence used in the answer.")

    with st.form("query_form"):
        sample = st.selectbox("Example question", SAMPLE_QUESTIONS)
        custom_question = st.text_input(
            "Or enter your own question",
            placeholder="Example: Which drugs treat lung cancer?",
        )
        query_options = st.columns([1, 1, 2])
        top_k = query_options[0].slider("Evidence items", 1, 10, 5)
        use_as_of = query_options[1].checkbox("Apply as-of date")
        as_of = query_options[2].date_input(
            "Knowledge cutoff",
            value=date(2023, 12, 31),
            min_value=date(2019, 1, 1),
            max_value=date.today(),
            disabled=not use_as_of,
        )
        submitted = st.form_submit_button("Ask memory agent", type="primary")

    if submitted:
        question = custom_question.strip() or sample
        if mode == DEMO_MODE:
            result = agent.answer(question, top_k=top_k, as_of=as_of if use_as_of else None)
            response = result.model_dump(mode="json")
            error = None
        else:
            payload = {
                "question": question,
                "top_k": top_k,
                "as_of": as_of.isoformat() if use_as_of else None,
            }
            response, error = api_request(api_url, "POST", "/v1/query", payload)

        if error:
            st.error(f"Could not query the backend: {error}")
        else:
            st.subheader("Grounded answer")
            st.markdown(f'<div class="status-card">{response["answer"]}</div>', unsafe_allow_html=True)
            st.subheader("Reasoning path")
            if response["reasoning_path"]:
                for index, path in enumerate(response["reasoning_path"], start=1):
                    st.write(f"{index}. `{path}`")
            else:
                st.caption("No graph path was found for this question.")
            st.subheader("Supporting evidence")
            if response["evidence"]:
                st.dataframe(
                    model_rows(response["evidence"]),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Try an entity represented in the synthetic graph, such as EGFR or osimertinib.")

with tabs[2]:
    st.header("Entity timeline")
    st.write("Trace how an entity appears in dated graph facts and their supporting sources.")

    if mode == DEMO_MODE:
        selected_entity = st.selectbox("Entity", demo_entities(agent))
    else:
        selected_entity = st.text_input("Entity", value="osimertinib")

    if selected_entity:
        if mode == DEMO_MODE:
            timeline = model_rows(agent.timeline(selected_entity))
            error = None
        else:
            timeline, error = api_request(
                api_url, "GET", f"/v1/timeline/{quote(selected_entity, safe='')}"
            )
            timeline = model_rows(timeline or [])

        if error:
            st.error(f"Could not load the timeline: {error}")
        elif timeline:
            first_date = timeline[0]["observed_at"]
            latest_date = timeline[-1]["observed_at"]
            timeline_metrics = st.columns(3)
            timeline_metrics[0].metric("Timeline events", len(timeline))
            timeline_metrics[1].metric("First observation", first_date)
            timeline_metrics[2].metric("Latest observation", latest_date)
            st.dataframe(timeline, width="stretch", hide_index=True)
        else:
            st.info("No dated facts were found for this entity.")

with tabs[3]:
    st.header("Evaluation")
    st.write(
        "Review deterministic extraction quality against labeled relations in the bundled "
        "synthetic biomedical dataset."
    )

    if mode == DEMO_MODE:
        report = agent.evaluate().model_dump(mode="json")
        error = None
    else:
        report, error = api_request(api_url, "GET", "/v1/evaluate")

    if error:
        st.warning("Connect to the FastAPI backend to load evaluation results.")
    else:
        metric_columns = st.columns(5)
        metric_columns[0].metric("Precision", f"{report['relation_precision']:.1%}")
        metric_columns[1].metric("Recall", f"{report['relation_recall']:.1%}")
        metric_columns[2].metric("F1 score", f"{report['relation_f1']:.1%}")
        metric_columns[3].metric(
            "Temporal accuracy", f"{report['temporal_order_accuracy']:.1%}"
        )
        metric_columns[4].metric("Consistency", f"{report['graph_consistency']:.1%}")

        st.subheader("Evaluation scope")
        records = load_synthetic_records()
        scope_columns = st.columns(3)
        scope_columns[0].metric("Records evaluated", report["records_evaluated"])
        scope_columns[1].metric(
            "Expected relations", sum(len(record.expected_relations) for record in records)
        )
        scope_columns[2].metric("Extractor", "Deterministic rules")
        st.dataframe(
            [
                {
                    "record_id": record.record_id,
                    "observed_at": record.observed_at.isoformat(),
                    "expected_relations": len(record.expected_relations),
                    "synthetic_text": record.text,
                }
                for record in records
            ],
            width="stretch",
            hide_index=True,
        )

with tabs[4]:
    st.header("Technical details")
    st.write("A concise view of the architecture, operating modes, and portfolio design choices.")

    architecture, modes = st.columns(2)
    with architecture:
        st.subheader("Data flow")
        st.code(
            """Synthetic biomedical records
    -> deterministic relation extraction
    -> dated graph facts
    -> NetworkX or Neo4j storage
    -> grounded answers and timelines""",
            language="text",
        )
    with modes:
        st.subheader("Operating modes")
        st.markdown(
            """
            | Mode | Graph access | External services |
            |---|---|---|
            | Self-contained demo | In-process NetworkX | None |
            | FastAPI backend | REST endpoints | FastAPI only |
            """
        )

    st.subheader("Engineering highlights")
    st.markdown(
        """
        - **Temporal provenance:** every relation retains an observation date, source ID, evidence text, and confidence.
        - **Explainability:** answers expose both supporting evidence and the traversed reasoning paths.
        - **Local-first defaults:** rules and synthetic data make the project reproducible without credentials or model downloads.
        - **Backend flexibility:** the same memory agent can use an in-memory graph or Neo4j Community Edition.
        - **Public-safe demo:** all displayed biomedical content is synthetic and intended for software demonstration.
        """
    )
    st.info(
        "This application is an engineering demonstration and is not a medical device "
        "or a source of clinical guidance."
    )
