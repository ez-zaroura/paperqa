import argparse
import json
import os
import re
import time
from pathlib import Path

from src.index import search
from src.llm import ask_llm
from src.rag import answer

HERE = Path(__file__).parent
QUESTIONS = HERE / "questions.json"
CACHE = HERE / "cache.json"
RESULTS_JSON = HERE / "results.json"
RESULTS_MD = HERE / "results.md"

REFUSAL = "je ne trouve pas la réponse"
HIT_KS = (1, 3, 5, 8)
MAX_K = max(HIT_KS)
MODEL = os.getenv("MODEL_NAME", "?")  # chargé depuis .env par src.llm
PAUSE = 1.0  # secondes d'attente après chaque appel au LLM (modifiable avec --pause)


# ---------- outils de notation ----------
def norm(text):
    text = text.replace(" ", " ").replace(" ", " ").lower()
    return re.sub(r"\s+", " ", text)


def is_refusal(text):
    return REFUSAL in norm(text)


def contains_all(text, groups):
    """Chaque groupe est une liste de variantes : au moins une doit apparaître."""
    t = norm(text)
    return all(any(alt.lower() in t for alt in group) for group in groups)


def cited_pages(text):
    return {int(n) for n in re.findall(r"p\.\s*(\d+)", text)}


def first_relevant_ranks(q):
    """Rangs (1 = meilleur) du premier passage attendu parmi les résultats de la recherche.

    - rang_page    : un passage de la bonne page est trouvé
    - rang_contenu : un passage de la bonne page contient en plus les chiffres/mots attendus
                     (plus exigeant : la page peut être la bonne alors que le morceau
                     retrouvé n'est pas celui qui contient la réponse)
    """
    res = search(q["question"], k=MAX_K)
    rank_page = rank_content = None
    for rank, (doc, meta) in enumerate(zip(res["documents"][0], res["metadatas"][0]), start=1):
        if meta["source"] != q["source"] or meta["page"] not in q["expected_pages"]:
            continue
        if rank_page is None:
            rank_page = rank
        if rank_content is None and contains_all(doc, q["must_contain"]):
            rank_content = rank
    return rank_page, rank_content


def grade_rag(q, text):
    refused = is_refusal(text)
    if q["should_refuse"]:
        return {"correct": refused, "false_refusal": False, "hallucination": not refused,
                "wrong": False, "citation_ok": None}
    if refused:
        return {"correct": False, "false_refusal": True, "hallucination": False,
                "wrong": False, "citation_ok": None}
    correct = contains_all(text, q["must_contain"])
    return {"correct": correct, "false_refusal": False, "hallucination": False,
            "wrong": not correct,
            "citation_ok": bool(cited_pages(text) & set(q["expected_pages"]))}


# ---------- cache ----------
def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def cached(cache, key, fn):
    if key not in cache:
        cache[key] = fn()
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(PAUSE)  # on ménage le quota gratuit
    return cache[key]


def pct(n, total):
    return f"{n}/{total}" + (f" ({100 * n / total:.0f} %)" if total else "")


# ---------- programme principal ----------
def main():
    global PAUSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", type=float, default=1.0,
                    help="secondes d'attente entre deux appels au LLM (ex. 10 si quota serré)")
    ap.add_argument("--k", type=int, default=8, help="nombre de passages donnés au LLM")
    ap.add_argument("--limit", type=int, help="ne garder que les N premières questions")
    ap.add_argument("--ids", help="ex. q01,q09 : ne garder que ces questions")
    ap.add_argument("--retrieval-only", action="store_true", help="mesurer seulement la recherche")
    ap.add_argument("--no-baseline", action="store_true", help="sauter la comparaison sans RAG")
    ap.add_argument("--fresh", action="store_true", help="ignorer le cache")
    args = ap.parse_args()
    PAUSE = args.pause

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    if args.ids:
        wanted = set(args.ids.split(","))
        questions = [q for q in questions if q["id"] in wanted]
    if args.limit:
        questions = questions[: args.limit]
    cache = {} if args.fresh else load_cache()

    rows = []
    for q in questions:
        row = {"id": q["id"], "type": q["type"], "question": q["question"],
               "rank": None, "rank_content": None}
        if q["expected_pages"]:
            row["rank"], row["rank_content"] = first_relevant_ranks(q)

        if not args.retrieval_only:
            try:
                rag = cached(cache, f"rag|{MODEL}|k={args.k}|{q['question']}",
                             lambda: answer(q["question"], k=args.k))
                row["rag_answer"] = rag["answer"]
                row["rag"] = grade_rag(q, rag["answer"])
                if not args.no_baseline and not q["should_refuse"]:
                    base = cached(cache, f"base|{MODEL}|{q['question']}",
                                  lambda: ask_llm(q["question"]))
                    row["base_answer"] = base
                    row["base_correct"] = contains_all(base, q["must_contain"])
            except Exception as e:  # ex. LLM indisponible : on continue
                row["error"] = str(e)[:200]
        rows.append(row)

        flags = [f"rang_page={row['rank'] or '-'}", f"rang_contenu={row['rank_content'] or '-'}"]
        if "rag" in row:
            r = row["rag"]
            flags.append("RAG=" + ("OK" if r["correct"] else "refus à tort" if r["false_refusal"]
                                    else "invention" if r["hallucination"] else "faux"))
            if r["citation_ok"] is not None:
                flags.append("cite=" + ("OK" if r["citation_ok"] else "KO"))
        if "base_correct" in row:
            flags.append("sans-RAG=" + ("OK" if row["base_correct"] else "KO"))
        if "error" in row:
            flags.append("ERREUR " + row["error"][:60])
        print(f"{q['id']} {q['type']:<12} " + "  ".join(flags))

    # ---------- résumé ----------
    answerable = [r for r, q in zip(rows, questions) if q["expected_pages"]]
    lines = [f"Évaluation PaperQA : {len(rows)} questions, k={args.k}, modèle={MODEL}", ""]
    lines.append("Recherche : la bonne PAGE est-elle dans les k premiers résultats ?")
    for k in HIT_KS:
        n = sum(1 for r in answerable if r["rank"] is not None and r["rank"] <= k)
        lines.append(f"  hit@{k}: {pct(n, len(answerable))}")
    lines.append("Recherche : le MORCEAU retrouvé contient-il la réponse (chiffres/mots attendus) ?")
    for k in HIT_KS:
        n = sum(1 for r in answerable if r["rank_content"] is not None and r["rank_content"] <= k)
        lines.append(f"  hit@{k} (contenu): {pct(n, len(answerable))}")

    done = [r for r in rows if "rag" in r]
    if done:
        ans = [r for r, q in zip(rows, questions) if "rag" in r and not q["should_refuse"]]
        traps = [r for r, q in zip(rows, questions) if "rag" in r and q["should_refuse"]]
        lines += ["", f"Réponses avec RAG (k={args.k})",
                  f"  correctes : {pct(sum(r['rag']['correct'] for r in ans), len(ans))}",
                  f"  refus à tort : {pct(sum(r['rag']['false_refusal'] for r in ans), len(ans))}",
                  f"  réponses fausses : {pct(sum(r['rag']['wrong'] for r in ans), len(ans))}"]
        cites = [r for r in ans if r["rag"]["citation_ok"] is not None]
        lines.append(f"  citation sur la bonne page : {pct(sum(r['rag']['citation_ok'] for r in cites), len(cites))}")
        if traps:
            lines.append(f"  pièges bien refusés : {pct(sum(r['rag']['correct'] for r in traps), len(traps))}"
                         f"  (inventions : {sum(r['rag']['hallucination'] for r in traps)})")
        for t in sorted({r["type"] for r in ans}):
            sub = [r for r in ans if r["type"] == t]
            lines.append(f"    - {t} : {pct(sum(r['rag']['correct'] for r in sub), len(sub))}")
        base = [r for r in rows if "base_correct" in r]
        if base:
            lines += ["", "Sans RAG (le LLM seul, même questions)",
                      f"  correctes : {pct(sum(r['base_correct'] for r in base), len(base))}"]

    summary = "\n".join(lines)
    print("\n" + summary)
    RESULTS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    RESULTS_MD.write_text("```\n" + summary + "\n```\n", encoding="utf-8")
    print(f"\nDétails (réponses complètes) : {RESULTS_JSON}")


if __name__ == "__main__":
    main()