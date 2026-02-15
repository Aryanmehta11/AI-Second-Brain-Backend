from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_service import ask_gemini
from app.services.vector_service import search_chunks

router = APIRouter(prefix="/ai", tags=["AI"])


class Question(BaseModel):
    question: str
    file_id: int   # IMPORTANT


@router.post("/ask-doc")
def ask_doc(data: Question):

    chunks = search_chunks(data.question, data.file_id)

    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant content found in this document")

    context = "\n\n".join(chunks)

    prompt = f"""
You are a document assistant.
Answer ONLY from the provided context.
If answer not present, say: "Answer not found in document".

CONTEXT:
{context}

QUESTION:
{data.question}
"""

    answer = ask_gemini(prompt)

    return {"answer": answer}
