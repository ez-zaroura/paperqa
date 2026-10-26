"""Serveur MCP : expose la recherche PaperQA comme outil pour un assistant IA.
"""
import contextlib
import os
import sys
from pathlib import Path

# Le client peut nous lancer depuis n'importe quel dossier : on se place à la racine du projet
# pour retrouver chroma_db/ et .env.
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402

# Les imports ci-dessous chargent le modèle d'embeddings : s'ils affichent quelque chose,
# cela doit aller sur stderr.
with contextlib.redirect_stdout(sys.stderr):
    from src.index import collection, search  # noqa: E402

MAX_K = 20

mcp = FastMCP("paperqa")


def format_passages(res):
    """Met en forme le résultat de search() : une entrée par passage, avec sa source."""
    docs, metas, dists = res["documents"][0], res["metadatas"][0], res["distances"][0]
    if not docs:
        return "Aucun passage trouvé."
    blocks = []
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
        text = " ".join(doc.split())  # retire les retours à la ligne inutiles
        blocks.append(f"[{rank}] [{meta['source']} p.{meta['page']}] (distance {dist:.2f})\n{text}")
    return "\n\n".join(blocks)


@mcp.tool()
def search_papers(question: str, k: int = 5) -> str:
    """Cherche dans les articles PDF indexés (PaperQA).

    Renvoie les k passages les plus proches de la question, chacun avec son fichier et sa page
    (format [fichier p.N]) et une distance (plus petite = plus proche). Utilise ces passages pour
    répondre en citant [fichier p.N] ; si aucun ne contient la réponse, dis-le.
    """
    question = question.strip()
    if len(question) < 3:
        return "Question trop courte."
    k = max(1, min(int(k), MAX_K))
    with contextlib.redirect_stdout(sys.stderr):
        if collection.count() == 0:
            return "L'index est vide : lance d'abord `python -m src.build_index`."
        res = search(question, k=k)
    return format_passages(res)


@mcp.tool()
def list_documents() -> str:
    """Liste les documents indexés et le nombre de morceaux de chacun."""
    with contextlib.redirect_stdout(sys.stderr):
        metas = collection.get(include=["metadatas"])["metadatas"]
    counts = {}
    for m in metas:
        counts[m["source"]] = counts.get(m["source"], 0) + 1
    if not counts:
        return "L'index est vide : lance d'abord `python -m src.build_index`."
    return "\n".join(f"{name} : {n} morceaux" for name, n in sorted(counts.items()))


if __name__ == "__main__":
    mcp.run()  # transport "stdio" par défaut