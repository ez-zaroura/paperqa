from src.ingest import read_pdf, chunk_text
from src.index import add_chunks, search

# Fonction qui construit les chunks à partir d'un PDF et d'une source
def build_chunks(path, source):
    chunks = []
    for page in read_pdf(path):
        for j, text in enumerate(chunk_text(page["text"] or "")):
            if len(text.strip()) < 150:
                continue
            chunks.append({
                "id": f"{source}-p{page['page']}-c{j}",
                "text": text,
                "source": source,
                "page": page["page"],
            })
    return chunks


if __name__ == "__main__":
    chunks = build_chunks("data/PDF2.pdf", "PDF2")
    print(len(chunks), "morceaux")
    add_chunks(chunks)
    while True:
        question = input("\nQuestion (vide pour quitter) : ")
        if not question:
            break
        results = search(question, k=6)
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            print(f"\n[{meta['source']} p.{meta['page']}]")
            print(doc)
        