# PaperQA

Assistant de questions-réponses sur des articles de recherche (PDF) : il retrouve les passages
pertinents, les donne à un LLM (Gemini) et répond **en citant le fichier et la page**.
Si la réponse n'est pas dans les documents, il le dit au lieu d'inventer.

Projet personnel (octobre 2026, en cours) pour apprendre à construire un système RAG de bout en bout :
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
  mcp_server.py    serveur MCP : la recherche exposée comme outil pour un assistant IA
  try_mcp_client.py  petit client pour tester le serveur MCP
  try_*.py         petits scripts de test manuel
eval/
  questions.json   20 questions annotées (réponse, pages, mots-clés attendus)
  run_eval.py      mesure la recherche et les réponses (avec / sans RAG)
  inspect_question.py   montre ce que la recherche renvoie pour une question
  show_answers.py       affiche les réponses jugées fausses à côté de l'attendu
  results.md / .json    résultats de la dernière évaluation complète
docs/
  rapport.tex           rapport technique (LaTeX)
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

Tests : `python -m pytest` (16 tests, sans appel réseau).

### Serveur MCP (optionnel)

`src/mcp_server.py` expose la recherche comme outil [MCP](https://modelcontextprotocol.io) :
un assistant IA compatible (Claude Desktop, Claude Code...) peut appeler `search_papers` et
`list_documents`, puis rédiger lui-même la réponse à partir des passages et de leurs pages.

```powershell
python -m src.try_mcp_client "votre question"   # test sans client MCP installé
```

Exemple de configuration d'un client (adapter les chemins) :

```json
{"mcpServers": {"paperqa": {"command": "C:\\chemin\\paperqa\\.venv\\Scripts\\python.exe",
                            "args": ["-m", "src.mcp_server"]}}}
```

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

### Résultat 2 : évaluation complète (20 questions, k = 8, `gemini-3.5-flash-lite`)

| Mesure | Avec RAG | Sans RAG (LLM seul) |
|---|---|---|
| Réponses correctes (17 questions avec réponse) | **16/17 (94 %)** | 1/17 (6 %) |
| Refus à tort | 0/17 | - |
| Réponses fausses | 1/17 | - |
| Citation de la bonne page | 17/17 (100 %) | - |
| Pièges bien refusés (3 questions sans réponse dans le document) | 3/3, aucune invention | - |

Par type de question (avec RAG) : factuelles 8/8, en français sur texte anglais 4/4, raisonnement 4/5.
Recherche (k = 8) : la bonne page est retrouvée 17 fois sur 17 ; le morceau qui contient la réponse
est retrouvé 16 fois sur 17 (hit@8 contenu, 94 %). Détails : `eval/results.md`, `eval/results.json`.

**Lecture du « sans RAG »** : le rapport date de 2026, donc le LLM seul ne peut pas connaître ses
chiffres et répond qu'ils ne sont pas disponibles ou en invente. Ce 1/17 montre surtout l'intérêt du
RAG pour des documents récents ou privés ; ce n'est pas une comparaison générale « RAG contre LLM ».
Le seul point trouvé sans RAG est une question d'explication (pourquoi la crise anglophone donne
beaucoup d'incidents peu mortels), qui ne demande pas de chiffre.

**Une erreur restante (q10)** : « comment diffèrent les projections 2026 du Mali et du Burkina Faso ? ».
Le système répond « plus de 40 % » et « baisse de 30 % », fidèle au texte retrouvé, alors que le rapport
donne 42 % et 27 % (probablement dans un tableau qui n'est pas dans les 8 morceaux retrouvés). Je la
garde comme erreur : c'est une vraie limite de la recherche sur les tableaux.

**Corrections de la notation** : après le premier passage complet, 2 des 3 réponses jugées fausses
l'étaient à cause de ma notation automatique, pas du système : un mot-clé écrit sans accent
(« Nigeria » / « Nigéria », la comparaison ignore maintenant les accents) et un chiffre exigé alors que
la question demandait une explication (q11, mots-clés remplacés par `anglophone` + `guérilla`).
Résultat avant correction : 14/17 ; après : 16/17. Les réponses elles-mêmes n'ont pas changé.

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

- Évaluation sur un seul rapport, un seul modèle et 17 questions avec réponse, que j'ai écrites moi-même :
  les pourcentages sont des ordres de grandeur, pas des garanties. La notation par mots-clés est
  imparfaite (voir les corrections ci-dessus) et demande une relecture manuelle des erreurs.
- Pas de gestion des PDF scannés (pas d'OCR) ; tableaux et figures sont lus comme du texte brut.
- Modèle d'embeddings orienté anglais : questions en français sur texte anglais non optimisées.

## Pistes

Modèle d'embeddings multilingue (comparaison mesurée), reranking, Docker et intégration continue
(GitHub Actions), exposition de la recherche comme outil MCP.