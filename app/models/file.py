from sqlalchemy import Column, Integer,String,ForeignKey
from app.db.database import Base
class File(Base):
    __tablename__="files"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filepath = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))