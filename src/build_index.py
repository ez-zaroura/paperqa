import argparse
from pathlib import Path

from src.index import add_chunks, collection
from src.ingest import chunk_text, read_pdf

MIN_CHUNK_CHARS = 150  # on jette les petits morceaux parasites (numéros de page, etc.)


def build_chunks(path, source, size=1200, overlap=200):
    chunks = []
    for page in read_pdf(path):
        text = page["text"] or ""
        for j, piece in enumerate(chunk_text(text, size, overlap)):
            if len(piece.strip()) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                {
                    "id": f"{source}-p{page['page']}-c{j}",
                    "text": piece,
                    "source": source,
                    "page": page["page"],
                }
            )
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=800, help="taille d'un chunk (caractères)")
    ap.add_argument("--overlap", type=int, default=150, help="chevauchement entre chunks")
    args = ap.parse_args()

    if collection.count() > 0:
        print(
            f"La base contient déjà {collection.count()} chunks. "
            "Supprime le dossier chroma_db puis relance, pour éviter les doublons."
        )
        return

    pdfs = sorted(Path("data").glob("*.pdf"))
    if not pdfs:
        print("Aucun PDF trouvé dans data/.")
        return

    print(f"Découpage : size={args.size}, overlap={args.overlap}")
    for pdf in pdfs:
        chunks = build_chunks(str(pdf), pdf.stem, args.size, args.overlap)
        add_chunks(chunks)
        print(f"{pdf.name} : {len(chunks)} chunks indexés")
    print(f"Total dans la base : {collection.count()} chunks")


if __name__ == "__main__":
    main()