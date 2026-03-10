from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.services.ai_service import ask_gemini
from app.services.vector_service import search_chunks
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.file import File as FileModel
from app.services.eval_service import run_evaluation

router=APIRouter(prefix='/ai',tags=["Evaluation"])


class EvalRequest(BaseModel):
    question:str
    file_id:int
    ground_truth:Optional[str]=None


@router.post("/evaluate")
def evaluate_rag(data:EvalRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    file=db.query(FileModel).filter(FileModel.id==data.file_id).first()
    if not file:
        raise HTTPException(status_code=404,detail="File not found")
    if file.user_id!=current_user.id:
        raise HTTPException(status_code=403,detail="Access Denied")
    
    chunks=search_chunks(db,data.question,data.file_id)
    context = "\n\n".join(chunks)
    prompt  = f"""You are a helpful document assistant.Use ONLY the following document context to answer.
    DOCUMENT CONTEXT: {context}
    USER QUESTION: {data.question}"""
    
    answer=ask_gemini(prompt)

    scores=run_evaluation(
        question=data.question, 
        answer=answer,
        contexts=context,
        ground_truth=data.ground_truth
    )

    def rate(score:float)->str:
        if score>=0.8: return "Excellent"
        if score>=0.6:  return "Good"
        return "Needs Improvement"
    
    return {
        "question":data.question,
        "answer":answer,
        "chunks_used":len(chunks),
        "scores":{
            metric:{
                "score":score,
                "rating":rate(score)
            }
            for metric,score in scores.items()
        }
    }

