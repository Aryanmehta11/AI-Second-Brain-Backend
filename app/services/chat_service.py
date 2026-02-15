from sqlalchemy.orm import Session
from app.models.message import Message

def save_message(db:Session,file_id:int,user_id:int,role:str,content:str):
    msg=Message(file_id=file_id,user_id=user_id,role=role,content=content)
    db.add(msg)
    db.commit()


def get_recent_message(db:Session,file_id:int,user_id:int,limit:int=5):
    return db.query(Message).filter(Message.file_id==file_id,Message.user_id==user_id).order_by(Message.id.desc()).limit(limit).all()[::-1]