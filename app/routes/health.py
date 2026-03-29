from fastapi import APIRouter, Response
router = APIRouter()
@router.get("/health")
def health():
    return {"status": "ok"}
@router.head("/health")
def health_head():
    return Response(status_code=200)