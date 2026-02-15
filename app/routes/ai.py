from fastapi import APIRouter, HTTPException,Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services.ai_service import ask_gemini
from app.services.vector_service import search_chunks
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.file import File as FileModel

router = APIRouter(prefix="/ai", tags=["AI"])


class Question(BaseModel):
    question: str
    file_id: int   # IMPORTANT


@router.post("/ask-doc")
def ask_doc(data: Question,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):

    file=db.query(FileModel).filter(FileModel.id==data.file_id).first()

    if not file:
        raise HTTPException(status_code=403,detail="File not found")
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403,detail="Access denied")

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
