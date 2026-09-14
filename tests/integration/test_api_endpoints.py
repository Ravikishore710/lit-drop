# Integration tests for FastAPI endpoints and local Qwen inference

import pytest
from fastapi.testclient import TestClient
from src.api.main import app, DOCUMENTS_DB
from src.llm.adapter import LLMOrchestrator


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_readiness_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_list_documents(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    first = docs[0]
    assert "document_id" in first
    assert "title" in first
    assert "page_count" in first


def test_search_endpoint(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "transformer attention mechanism", "top_k": 5},
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)


def test_compare_documents_validation(client):
    response = client.post(
        "/api/v1/compare",
        json={"document_ids": ["doc1"], "query": "compare attention mechanisms"},
    )
    assert response.status_code == 400


def test_compare_documents_execution(client):
    list_res = client.get("/api/v1/documents")
    docs = list_res.json()
    if len(docs) >= 2:
        d1 = docs[0]["document_id"]
        d2 = docs[1]["document_id"]
        response = client.post(
            "/api/v1/compare",
            json={"document_ids": [d1, d2], "query": "attention architecture", "top_k": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "status" in data
        assert "citations" in data


def test_local_qwen_orchestration():
    orch = LLMOrchestrator()
    query = "What is the primary mechanism described?"
    evidence = "[SRC_01] The Transformer model uses scaled dot-product attention."
    ans = orch.generate_grounded_answer(query=query, evidence_bundle=evidence, force_local=True)
    assert ans is not None
    assert len(ans) > 0
