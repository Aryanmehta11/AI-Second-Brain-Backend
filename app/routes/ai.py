from fastapi import APIRouter, HTTPException,Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services.ai_service import ask_gemini
from app.services.vector_service import search_chunks
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.file import File as FileModel
from app.services.chat_service import get_recent_message, save_message
from app.models.message import Message
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db


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

    history=get_recent_message(db,data.file_id,current_user.id)

    conversation=''
    for msg in history:
        conversation+=f"{msg.role.upper()}:\n{msg.content}\n\n"

    prompt = f"""
You are a helpful document assistant.

Conversation so far:
{conversation}

Use ONLY the following document context to answer.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{data.question}
"""

    answer = ask_gemini(prompt)
    save_message(db,file.id,current_user.id,'user',data.question)
    save_message(db,file.id,current_user.id,'assistant',answer)

    return {"answer": answer}



@router.get("/history/{file_id}")
def get_history(file_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    file=db.query(FileModel).filter(FileModel.id==file_id).first()
    if not file:
        raise HTTPException(status_code=403,detail="File not found")
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403,detail="Access denied")
    messages=db.query(Message).filter(Message.file_id==file_id,Message.user_id==current_user.id).order_by(Message.id.desc()).all()[::-1]
    return [
        {"role":m.role,"content":m.content} for m in messages
    ]