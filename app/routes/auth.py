from fastapi import APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import Token, UserCreate, UserLogin
from app.services.auth_service import register_user, authenticate_user

router=APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(data:UserCreate,db:Session=Depends(get_db)):
    user=register_user(db,data.email,data.password)
    return {"message":"User registered successfully","user_id": user.id}

@router.post("/login", response_model=Token)
def Login(data:UserLogin,db:Session=Depends(get_db)):
    token = authenticate_user(db, data.email, data.password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token}

    

