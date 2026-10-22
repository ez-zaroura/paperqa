from fastapi.testclient import TestClient

import src.api as api

client = TestClient(api.app)


class FakeCollection:
    def __init__(self, n):
        self.n = n

    def count(self):
        return self.n


def test_health(monkeypatch):
    monkeypatch.setattr(api, "collection", FakeCollection(42))
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "chunks": 42}


def test_ask_formats_sources(monkeypatch):
    monkeypatch.setattr(api, "collection", FakeCollection(10))
    monkeypatch.setattr(
        api, "answer",
        lambda q, k=8: {"answer": "Réponse", "sources": [("PDF2", 2), ("PDF2", 5)]},
    )
    r = client.post("/ask", json={"question": "Quelle est la méthode ?"})
    assert r.status_code == 200
    assert r.json() == {"answer": "Réponse", "sources": ["PDF2 p.2", "PDF2 p.5"]}


def test_ask_rejects_too_short_question():
    r = client.post("/ask", json={"question": "a"})
    assert r.status_code == 422


def test_ask_empty_index_returns_503(monkeypatch):
    monkeypatch.setattr(api, "collection", FakeCollection(0))
    r = client.post("/ask", json={"question": "Une question valide"})
    assert r.status_code == 503


def test_ask_llm_failure_returns_503(monkeypatch):
    monkeypatch.setattr(api, "collection", FakeCollection(10))

    def boom(q, k=8):
        raise Exception("503 high demand")

    monkeypatch.setattr(api, "answer", boom)
    r = client.post("/ask", json={"question": "Une question valide"})
    assert r.status_code == 503