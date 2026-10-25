```
Évaluation PaperQA : 20 questions, k=8, modèle=gemini-3.5-flash-lite

Recherche : la bonne PAGE est-elle dans les k premiers résultats ?
  hit@1: 9/17 (53 %)
  hit@3: 15/17 (88 %)
  hit@5: 17/17 (100 %)
  hit@8: 17/17 (100 %)
Recherche : le MORCEAU retrouvé contient-il la réponse (chiffres/mots attendus) ?
  hit@1 (contenu): 5/17 (29 %)
  hit@3 (contenu): 12/17 (71 %)
  hit@5 (contenu): 14/17 (82 %)
  hit@8 (contenu): 16/17 (94 %)

Réponses avec RAG (k=8)
  correctes : 16/17 (94 %)
  refus à tort : 0/17 (0 %)
  réponses fausses : 1/17 (6 %)
  citation sur la bonne page : 17/17 (100 %)
  pièges bien refusés : 3/3 (100 %)  (inventions : 0)
    - factuelle : 8/8 (100 %)
    - francais : 4/4 (100 %)
    - raisonnement : 4/5 (80 %)

Sans RAG (le LLM seul, même questions)
  correctes : 1/17 (6 %)
```
