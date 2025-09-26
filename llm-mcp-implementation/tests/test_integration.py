# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.skipif(True, reason="Enable only when Ollama server is running locally")
def test_integration_chat():
    resp = client.post("/chat", json={"prompt":"What is a loan?"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("response"), str)
    assert len(data["response"]) > 0
