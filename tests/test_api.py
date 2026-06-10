from fastapi.testclient import TestClient

from src.app.api.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "biomed-kg-memory-agent"
    assert response.json()["openai_required"] is False


def test_query_endpoint_returns_grounded_evidence():
    with TestClient(app) as client:
        response = client.post(
            "/v1/query",
            json={"question": "What treats lung cancer with EGFR?", "top_k": 2},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["evidence"]
    assert "graph memory" in data["answer"].lower()


def test_evaluation_endpoint():
    with TestClient(app) as client:
        response = client.get("/v1/evaluate")

    assert response.status_code == 200
    assert response.json()["records_evaluated"] == 4
