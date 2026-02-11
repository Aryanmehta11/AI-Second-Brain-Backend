from sqlalchemy import Column, Integer,String
from app.db.database import Base
class File(Base):
    __tablename__="files"
    id=Column(Integer,primary_key=True)
    filename=Column(String)
    filepath=Column(String)