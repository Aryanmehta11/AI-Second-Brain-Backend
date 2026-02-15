from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.security import SECRET_KEY,ALGORITHM
security=HTTPBearer()

def get_current_user(
        credentials:HTTPAuthorizationCredentials=Depends(security),
        db:Session=Depends(get_db)
):
    token=credentials.credentials
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id=payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid token")
    user=db.query(User).filter(User.id==user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found")
    return user