"""Affiche les réponses du RAG à côté de la réponse attendue, pour les relire à la main.

Depuis la racine du projet :

    python -m eval.show_answers            # toutes les questions notées "pas correctes"
    python -m eval.show_answers q10 q11    # les questions de ton choix

Utilise eval/results.json (écrit par run_eval) et eval/questions.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def main():
    questions = {q["id"]: q for q in json.loads((HERE / "questions.json").read_text(encoding="utf-8"))}
    rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))

    wanted = sys.argv[1:]
    if wanted:
        rows = [r for r in rows if r["id"] in wanted]
    else:
        rows = [r for r in rows if "rag" in r and not r["rag"]["correct"]]

    if not rows:
        print("Rien à afficher.")
        return

    for r in rows:
        q = questions[r["id"]]
        print("=" * 80)
        print(f"{r['id']} ({r['type']}) : {q['question']}")
        print(f"\nATTENDU : {q['expected_answer']}")
        print(f"MOTS-CLÉS exigés (une variante par groupe) : {q['must_contain']}")
        print(f"\nRÉPONSE DU RAG :\n{r.get('rag_answer', '(pas de réponse enregistrée)')}")
        print(f"\nrang_page={r['rank']}  rang_contenu={r['rank_content']}  notation={r.get('rag')}")
    print("=" * 80)


if __name__ == "__main__":
    main()