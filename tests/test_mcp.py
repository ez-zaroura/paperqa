"""Tests du serveur MCP (sans réseau, sans vraie base)"""
from src import mcp_server


class FakeCollection:
    def __init__(self, n=2):
        self.n = n

    def count(self):
        return self.n

    def get(self, include=None):
        return {"metadatas": [{"source": "PDF3", "page": 1}, {"source": "PDF3", "page": 2},
                              {"source": "PDF2", "page": 5}][: self.n]}


def fake_search(question, k=4):
    fake_search.last_k = k
    return {"documents": [["Il y a eu 413\névénements."]],
            "metadatas": [[{"source": "PDF3", "page": 2}]],
            "distances": [[0.31]]}


def test_search_formats_source_and_page(monkeypatch):
    monkeypatch.setattr(mcp_server, "collection", FakeCollection())
    monkeypatch.setattr(mcp_server, "search", fake_search)
    out = mcp_server.search_papers("combien d'événements ?")
    assert "[PDF3 p.2]" in out and "413 événements" in out and "0.31" in out


def test_search_limits_k(monkeypatch):
    monkeypatch.setattr(mcp_server, "collection", FakeCollection())
    monkeypatch.setattr(mcp_server, "search", fake_search)
    mcp_server.search_papers("une question", k=500)
    assert fake_search.last_k == mcp_server.MAX_K


def test_search_rejects_short_question(monkeypatch):
    monkeypatch.setattr(mcp_server, "collection", FakeCollection())
    assert "trop courte" in mcp_server.search_papers("a")


def test_search_empty_index(monkeypatch):
    monkeypatch.setattr(mcp_server, "collection", FakeCollection(0))
    assert "index est vide" in mcp_server.search_papers("une question")


def test_list_documents(monkeypatch):
    monkeypatch.setattr(mcp_server, "collection", FakeCollection(3))
    out = mcp_server.list_documents()
    assert "PDF3 : 2 morceaux" in out and "PDF2 : 1 morceaux" in out