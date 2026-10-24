import json
import sys
from pathlib import Path

from eval.run_eval import contains_all
from src.index import search

QUESTIONS = Path(__file__).parent / "questions.json"


def main():
    if len(sys.argv) < 2:
        print("Usage : python -m eval.inspect_question q03 [k]")
        return
    qid = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    q = next((x for x in questions if x["id"] == qid), None)
    if q is None:
        print(f"Question {qid} introuvable.")
        return

    print(q["question"])
    print(f"Attendu : {q['expected_answer']}  (pages {q['expected_pages']})\n")

    res = search(q["question"], k=k)
    for rank, (doc, meta, dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), start=1
    ):
        page_ok = meta["source"] == q["source"] and meta["page"] in q["expected_pages"]
        has_answer = bool(q["must_contain"]) and contains_all(doc, q["must_contain"])
        mark = "RÉPONSE ICI" if page_ok and has_answer else "bonne page" if page_ok else ""
        print(f"{rank:2d}. {meta['source']} p.{meta['page']}  distance={dist:.3f}  {mark}")
        text = doc.replace("\n", " ")
        print("    " + (text[:700] if page_ok else text[:100]) + ("" if len(text) <= 700 else " …"))


if __name__ == "__main__":
    main()