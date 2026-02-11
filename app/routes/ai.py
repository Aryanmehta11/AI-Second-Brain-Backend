from fastapi import APIRouter 
from pydantic import BaseModel
from app.services.ai_service import ask_gemini


router = APIRouter(prefix="/ai", tags=["AI"])
class Question(BaseModel):
    question: str
@router.post("/ask")
def ask_ai(question: Question):
    answer=ask_gemini(question.question)
    return {"answer": answer}
