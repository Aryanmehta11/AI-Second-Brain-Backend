from sqlalchemy import Column, Integer,String,ForeignKey, Text
from app.db.database import Base

class Message(Base):
    __tablename__="messages"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    role = Column(Text)   
    content = Column(Text)
