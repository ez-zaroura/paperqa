import fitz  # PyMuPDF
from pypdf import PdfReader

path = "data/PDF2.pdf"
print("--- pypdf ---")
print(PdfReader(path).pages[4].extract_text())
print("--- pymupdf ---")
print(fitz.open(path)[4].get_text())