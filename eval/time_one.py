"""Mesure où passe le temps pour UNE question : recherche, RAG complet, LLM seul.
"""
import time

from src.index import search
from src.llm import ask_llm
from src.rag import answer

QUESTION = "How many violent events and fatalities did West Africa experience in 2025?"


def timed(label, fn):
    start = time.time()
    result = fn()
    print(f"{label:<22} {time.time() - start:5.1f} s", end="")
    if isinstance(result, str):
        print(f"   ({len(result)} caractères)")
    elif isinstance(result, dict) and "answer" in result:
        print(f"   ({len(result['answer'])} caractères)")
    else:
        print()
    return result


if __name__ == "__main__":
    timed("recherche seule", lambda: search(QUESTION, k=8))
    timed("RAG complet", lambda: answer(QUESTION, k=8))
    timed("LLM seul (sans RAG)", lambda: ask_llm(QUESTION))