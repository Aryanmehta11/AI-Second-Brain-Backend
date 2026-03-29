from fastapi import APIRouter, Response,Depends
from requests import Session
from sqlalchemy import text

from app.db.database import get_db
router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.head("/health")
def health_head():
    return Response(status_code=200)

@router.get("/db-health")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

@router.head("/db-health")
def db_health_head():
    return Response(status_code=200)