# test_hybrid.py
from dotenv import load_dotenv
load_dotenv()

from app.db.database import SessionLocal
from app.services.vector_service import search_chunks, hybrid_search_chunks

db = SessionLocal()

# Using file 24 — 76 chunks, best for comparison
question = "What is Toyota Financial Services scorecard?"
file_id  = 24

print("=" * 50)
print("OLD — Vector search only:")
old_results = search_chunks(db, question, file_id)
for i, chunk in enumerate(old_results, 1):
    print(f"  [{i}] {chunk[:150]}")

print("\n" + "=" * 50)
print("NEW — Hybrid search:")
new_results = hybrid_search_chunks(db, question, file_id)
for i, chunk in enumerate(new_results, 1):
    print(f"  [{i}] {chunk[:150]}")

db.close()