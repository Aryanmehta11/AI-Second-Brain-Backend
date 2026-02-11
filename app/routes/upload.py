from fastapi import APIRouter,UploadFile,File,Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.file import File as FileModel
import os
import shutil
from app.routes.ai import Question
from app.services.chunk_service import chunk_service
from app.services.vector_service  import search_chunks
from app.services.pdf_service import extract_text
from app.services.ai_service import ask_gemini

router=APIRouter(prefix='/upload',tags=["upload"])
UPLOAD_DIR="uploads"
os.makedirs(UPLOAD_DIR,exist_ok=True)

@router.post("/")
def upload_file(file:UploadFile=File(...),db:Session=Depends(get_db)):
    path=f"{UPLOAD_DIR}/{file.filename}"

    with open(path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    new_file=FileModel(filename=file.filename,filepath=path)
    db.add(new_file)
    db.commit()

    text=extract_text(path)
    summary = ask_gemini(f"Summarize this:\n{text[:4000]}")
    return {"summary": summary}

      


@router.post("/ask-doc")
def ask_doc(data: Question):
    chunks = search_chunks(data.question)

    context = "\n".join(chunks)

    prompt = f"""
    Answer using ONLY this context:

    {context}

    Question: {data.question}
    """

    answer = chunk_service(prompt)

    return {"answer": answer}
