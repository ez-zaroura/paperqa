import os
from time import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

def ask_llm(prompt, retries=3):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquante : vérifie ton fichier .env")
    client = genai.Client(api_key=api_key)

    for attempt in range(retries):
        try:
            interaction = client.interactions.create(
                model=os.getenv("MODEL_NAME"), input=prompt
            )
            return interaction.output_text
        except Exception as e:
            temporary = "503" in str(e) or "429" in str(e)
            if not temporary or attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))  # attend 2 s, puis 4 s