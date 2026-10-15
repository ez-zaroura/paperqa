from pypdf import PdfReader

# Fonction qui lit un PDF et retourne une liste de pages avec leur texte
def read_pdf(path):
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append({"page": i + 1, "text": page.extract_text()})
    return pages

# Fonction qui découpe un texte en morceaux de taille maximale "size" avec un chevauchement "overlap"
def chunk_text(text, size=800, overlap=150):
    if overlap >= size:
        raise ValueError("overlap doit être plus petit que size")
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


if __name__ == "__main__":
    pages = read_pdf("data/PDF1.pdf")
    print(len(pages), "pages")
    print(pages[0]["text"][:500])