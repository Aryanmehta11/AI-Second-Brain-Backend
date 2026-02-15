from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from app.db.database import get_db
from app.models.file import File as FileModel

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunk_service import chunk_text
from app.services.vector_service import add_chunks
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/")
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # 1️⃣ Validate file
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # 2️⃣ Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 3️⃣ Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4️⃣ Save metadata to DB
        new_file = FileModel(filename=filename, filepath=file_path, user_id=current_user.id)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        # 5️⃣ Extract text from PDF
        text = extract_text_from_pdf(file_path)

        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF has no readable text")

        # 6️⃣ Chunk text
        chunks = chunk_text(text)

        # 7️⃣ Store embeddings in vector DB
        add_chunks(chunks, new_file.id)

        return {
            "message": "File uploaded and processed successfully",
            "file_id": new_file.id,
            "chunks_created": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
