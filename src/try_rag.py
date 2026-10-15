from src.index import collection
from src.rag import answer

if __name__ == "__main__":
    if collection.count() == 0:
        print("La base est vide : lance d'abord python -m src.try_search")
        raise SystemExit

    while True:
        question = input("\nQuestion (vide pour quitter) : ")
        if not question:
            break
        result = answer(question, k=8)
        print("\n" + result["answer"])
        print("\nPassages consultés :", ", ".join(f"{s} p.{p}" for s, p in result["sources"]))