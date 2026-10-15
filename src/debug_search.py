from src.index import search

if __name__ == "__main__":
    question = input("Question : ")
    results = search(question, k=15)
    for rank, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0]),
        start=1,
    ):
        print(f"{rank:2d}. p.{meta['page']}  distance={dist:.3f}  {doc[:120]!r}")