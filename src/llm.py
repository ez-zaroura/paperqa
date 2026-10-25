import os
import threading
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()


def _call_with_timeout(fn, seconds):
    """Lance fn() et abandonne si elle ne répond pas en `seconds` secondes."""
    box = {}

    def run():
        try:
            box["value"] = fn()
        except Exception as e:  # on remonte l'erreur dans le thread principal
            box["error"] = e

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise TimeoutError(
            f"Pas de réponse de Gemini après {seconds} s "
            "(souvent un quota dépassé, erreur 429 : attends quelques minutes)"
        )
    if "error" in box:
        raise box["error"]
    return box["value"]


def ask_llm(prompt, retries=4, timeout=120):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquante : vérifie ton fichier .env")
    client = genai.Client(api_key=api_key)
    model = os.getenv("MODEL_NAME")

    for attempt in range(retries):
        try:
            return _call_with_timeout(
                lambda: client.interactions.create(model=model, input=prompt).output_text,
                timeout,
            )
        except Exception as e:
            temporary = isinstance(e, TimeoutError) or "503" in str(e) or "429" in str(e)
            if not temporary or attempt == retries - 1:
                raise
            wait = 10 * (attempt + 1)  # modèle surchargé : on laisse le temps de se calmer
            print(f"[llm] tentative {attempt + 1}/{retries} échouée ({str(e)[:80]}), "
                  f"nouvel essai dans {wait} s")
            time.sleep(wait)