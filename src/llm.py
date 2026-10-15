import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def ask_llm(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquante : vérifie ton fichier .env")
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=os.getenv("MODEL_NAME"),
        input=prompt,
    )
    return interaction.output_text