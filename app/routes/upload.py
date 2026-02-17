from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from app.db.database import get_db
from app.models import file
from app.models.file import File as FileModel

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunk_service import chunk_text
from app.services.vector_service import add_chunks
from app.core.dependencies import get_current_user
from app.models.message import Message
from app.services.vector_service import delete_chunks
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
        new_file = FileModel(filename=filename, original_name=file.filename, user_id=current_user.id)
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
        add_chunks(db, chunks, new_file.id)


        return {
            "message": "File uploaded and processed successfully",
            "file_id": new_file.id,
            "chunks_created": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/files")
def list_files(db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    files=db.query(FileModel).filter(FileModel.user_id==current_user.id).all()
    return [{"id": f.id, "filename": f.original_name} for f in files]


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1️⃣ Find file
    file = db.query(FileModel).filter(FileModel.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # 2️⃣ Ownership check
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 3️⃣ Delete physical file
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    # 4️⃣ Delete vector embeddings
    delete_chunks(file_id)

    # 5️⃣ Delete chat history
    db.query(Message).filter(Message.file_id == file_id).delete()

    # 6️⃣ Delete DB record
    db.delete(file)
    db.commit()

    return {"message": "File deleted successfully"}