from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.index import collection
from src.rag import answer

app = FastAPI(title="PaperQA")


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    k: int = Field(default=8, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "chunks": collection.count()}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if collection.count() == 0:
        raise HTTPException(status_code=503, detail="Index vide : lance d'abord src.try_search.")
    try:
        result = answer(req.question, k=req.k)
    except RuntimeError as e:  # config : clé manquante, etc.
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:  # LLM indisponible, quota, etc.
        raise HTTPException(status_code=503, detail=f"LLM indisponible : {e}")

    return {
        "answer": result["answer"],
        "sources": [f"{source} p.{page}" for source, page in result["sources"]],
    }