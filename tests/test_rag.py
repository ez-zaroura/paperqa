from src.rag import answer, build_prompt


def test_prompt_contains_question_and_passages():
    passages = [("Le modèle utilise la métrique AUC.", "bus", 3)]
    prompt = build_prompt("Quelle métrique ?", passages)
    assert "Quelle métrique ?" in prompt
    assert "Le modèle utilise la métrique AUC." in prompt
    assert "[bus p.3]" in prompt


def test_answer_returns_answer_and_sources(monkeypatch):
    fake_results = {
        "documents": [["Texte A", "Texte B"]],
        "metadatas": [[{"source": "bus", "page": 1}, {"source": "bus", "page": 2}]],
    }
    monkeypatch.setattr("src.rag.search", lambda question, k=8: fake_results)
    monkeypatch.setattr("src.rag.ask_llm", lambda prompt: "Réponse factice")

    result = answer("Une question ?")

    assert result["answer"] == "Réponse factice"
    assert result["sources"] == [("bus", 1), ("bus", 2)]