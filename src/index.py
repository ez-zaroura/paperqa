import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("articles")

def add_chunks(chunks):
    # chunks = liste de dicts : {"id": ..., "text": ..., "source": ..., "page": ...}
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],
    )

def search(question, k=4):
    q_emb = model.encode([question]).tolist()
    return collection.query(query_embeddings=q_emb, n_results=k)