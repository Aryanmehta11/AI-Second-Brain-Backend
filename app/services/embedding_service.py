import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: no configure(), only Client()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts
    )

    return [e.values for e in response.embeddings]
