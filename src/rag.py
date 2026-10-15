from src.index import search
from src.llm import ask_llm


def build_prompt(question, passages):
    # passages : liste de tuples (texte, source, page)
    context = "\n\n".join(
        f"[{source} p.{page}]\n{text}" for text, source, page in passages
    )
    return (
        "Tu réponds à une question à partir d'extraits d'articles.\n"
        "Règles :\n"
        "- Utilise uniquement les extraits ci-dessous.\n"
        "- Si la réponse ne s'y trouve pas, réponds exactement : "
        "\"Je ne trouve pas la réponse dans les documents.\"\n"
        "- Cite tes sources sous la forme [fichier p.N] après chaque affirmation.\n"
        "- Réponds dans la langue de la question.\n\n"
        f"EXTRAITS :\n{context}\n\n"
        f"QUESTION : {question}\n"
        "RÉPONSE :"
    )


def answer(question, k=8):
    results = search(question, k=k)
    passages = [
        (doc, meta["source"], meta["page"])
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]
    prompt = build_prompt(question, passages)
    sources = list(dict.fromkeys((source, page) for _, source, page in passages))
    return {"answer": ask_llm(prompt), "sources": sources}