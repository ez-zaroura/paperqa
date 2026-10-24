
Assistant de questions-réponses sur des articles de recherche (PDF) : il retrouve les passages
pertinents, les donne à un LLM (Gemini) et répond **en citant le fichier et la page**.
Si la réponse n'est pas dans les documents, il le dit au lieu d'inventer.

Projet personnel (octobre 2026) pour apprendre à construire un système RAG de bout en bout :
ingestion, recherche vectorielle, génération, API, tests et **évaluation chiffrée**.

## Comment ça marche

```
INDEXATION (une fois)
  PDF  ->  pages (PyMuPDF)  ->  morceaux de 1200 caractères (chevauchement 200)
       ->  embeddings (all-MiniLM-L6-v2)  ->  base vectorielle Chroma

QUESTION (à chaque requête)
  question -> embedding -> les k=8 morceaux les plus proches
           -> prompt (consignes + extraits + question) -> Gemini
           -> réponse avec citations [fichier p.N]
```

Le prompt impose au LLM de n'utiliser que les extraits fournis et de répondre
« Je ne trouve pas la réponse dans les documents. » quand l'information est absente.

## Structure du dépôt

```
src/
  ingest.py        lecture des PDF et découpage en morceaux
  index.py         embeddings + base Chroma (add_chunks, search)
  build_index.py   indexe tous les PDF de data/ (taille des morceaux réglable)
  llm.py           appel à Gemini (délai maximum, réessais)
  rag.py           construction du prompt et réponse avec sources
  api.py           API FastAPI (POST /ask, GET /health)
  try_*.py         petits scripts de test manuel
eval/
  questions.json   20 questions annotées (réponse, pages, mots-clés attendus)
  run_eval.py      mesure la recherche et les réponses (avec / sans RAG)
  inspect_question.py   montre ce que la recherche renvoie pour une question
tests/             tests unitaires (pytest)
```

## Installation

Python 3.13 recommandé. Depuis la racine du projet (PowerShell) :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crée un fichier `.env` à partir de `.env.example` et mets-y ta clé Gemini
(gratuite sur Google AI Studio). **Ne commite jamais `.env`.**

Place tes PDF dans `data/` (le nom du fichier devient la source citée : `data/PDF3.pdf` -> `PDF3`).

## Utilisation

```powershell
# 1. Indexer les PDF (supprime d'abord chroma_db/ pour repartir de zéro)
python -m src.build_index

# 2. Lancer l'API
python -m uvicorn src.api:app --reload
# puis ouvrir http://127.0.0.1:8000/docs
```

Exemple de requête `POST /ask` :

```json
{"question": "How many violent events and fatalities were recorded in North Africa in 2025?", "k": 8}
```

Réponse obtenue pendant l'évaluation :

```
In 2025, 413 violent events resulting in 360 fatalities were recorded in North Africa
across Algeria, Libya, Morocco, and Tunisia [PDF3 p.2].
```

Tests : `python -m pytest` (11 tests, sans appel réseau).

## Évaluation

Corpus d'évaluation : un rapport de 21 pages (*Changing Geographies of Violence in North and
West Africa*), 20 questions écrites à la main dans `eval/questions.json` :
8 factuelles, 5 de raisonnement (plusieurs passages), 4 en français sur un texte anglais,
3 pièges (réponse absente ou hors sujet). Chaque question a la ou les pages attendues et des
mots-clés qui doivent apparaître dans la réponse. Les faits attendus ont été vérifiés dans le
texte du PDF.

Mesures :
- **hit@k (page)** : une partie de la bonne page est dans les k premiers résultats ;
- **hit@k (contenu)** : le morceau retrouvé contient lui-même la réponse (plus exigeant) ;
- **réponses correctes**, **refus à tort**, **inventions** (sur les pièges), **citation de la bonne page** ;
- comparaison **avec RAG / sans RAG** (le LLM seul).

### Résultat 1 : taille des morceaux (recherche seule, 17 questions avec réponse)

hit@k (contenu) : le morceau retrouvé contient la réponse.

| Découpage (taille / chevauchement) | hit@3 | hit@5 | hit@8 |
|---|---|---|---|
| 350 / 70 | 10/17 | 11/17 | 12/17 |
| 500 / 100 | 6/17 | 11/17 | 11/17 |
| 800 / 150 | 10/17 | 12/17 | 15/17 |
| **1200 / 200** (retenu) | **12/17** | **14/17** | **16/17** |

Exemple : à 800/150, la question sur le nombre de décès par événement (q03) était refusée à tort :
la bonne page était retrouvée, mais le morceau contenant la phrase « 2,4 puis 2,1 » était mélangé à un
autre paragraphe et classé trop bas. Avec 1200/200, la réponse est correcte.
Limite : la mesure exige que tous les chiffres attendus soient dans le même morceau, ce qui
avantage un peu les grands morceaux.

### Résultat 2 : avec et sans RAG

Sur q01 à q03, le LLM seul (sans documents) répond que les chiffres de 2025 « ne sont pas encore
disponibles » ou invente une valeur (2,3 à 2,9 décès par événement, alors que le rapport donne 2,1).
Avec RAG, les trois réponses sont correctes et citent la bonne page.

<!-- À COMPLÉTER après `python -m eval.run_eval` (résultats complets, 20 questions) -->

| Mesure | Valeur |
|---|---|
| Réponses correctes avec RAG | ?/17 |
| Refus à tort | ?/17 |
| Citation sur la bonne page | ?/? |
| Pièges bien refusés | ?/3 |
| Réponses correctes sans RAG | ?/17 |

## Ce que j'ai appris / problèmes rencontrés

- **Un RAG peut échouer sans que le LLM soit en cause** : un refus à tort venait de la recherche
  (le bon passage était classé 6e alors que seuls 4 passages étaient transmis). D'où k = 8 et
  un outil (`inspect_question`) pour regarder ce que la recherche renvoie.
- **La qualité de l'extraction du PDF compte** : avec `pypdf`, le texte d'un des articles sortait
  sans espaces entre les mots ; passage à PyMuPDF.
- **La taille des morceaux se choisit en mesurant**, pas au hasard (tableau ci-dessus).
- **Quota gratuit** : l'API Gemini renvoie des erreurs 429 en cas d'appels trop rapprochés ; les
  réponses sont mises en cache (`eval/cache.json`) et le script d'évaluation accepte `--pause`.

## Limites

- Évaluation sur un seul rapport et 17 questions avec réponse : les pourcentages sont à lire comme
  des ordres de grandeur ; la notation par mots-clés est stricte et demande une relecture manuelle.
- Pas de gestion des PDF scannés (pas d'OCR) ; tableaux et figures sont lus comme du texte brut.
- Modèle d'embeddings orienté anglais : questions en français sur texte anglais non optimisées.

## Pistes

Modèle d'embeddings multilingue (comparaison mesurée), reranking, Docker et intégration continue
(GitHub Actions), exposition de la recherche comme outil MCP.