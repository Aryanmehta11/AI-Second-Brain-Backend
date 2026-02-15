from fastapi import FastAPI
from app.routes import health,ai,upload,auth
from app.models import user,file
from app.db.database import Base,engine
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id":user_id}

@app.get("/search")
def search(q:str):
    return {"query": q}

app.include_router(ai.router)
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(auth.router)