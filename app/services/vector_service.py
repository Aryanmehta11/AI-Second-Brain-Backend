from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import embed_texts


# ---------------- ADD CHUNKS ----------------
def add_chunks(db: Session, chunks: list[str], file_id: int):
    embeddings = embed_texts(chunks)

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        db.execute(
            text("""
                INSERT INTO document_chunks (id, file_id, content, embedding)
                VALUES (:id, :file_id, :content, CAST(:embedding AS vector))
            """),
            {
                "id": f"{file_id}_{i}",
                "file_id": file_id,
                "content": chunk,
                "embedding": str(emb)
            }
        )

    db.commit()


# ---------------- SEARCH SINGLE DOC ----------------
def search_chunks(db: Session, query: str, file_id: int, k: int = 4):
    query_embedding = embed_texts([query])[0]

    result = db.execute(
        text("""
            SELECT content
            FROM document_chunks
            WHERE file_id = :file_id
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :k
        """),
        {"file_id": file_id, "embedding": str(query_embedding), "k": k}
    )

    return [row[0] for row in result.fetchall()]


# ---------------- SEARCH ALL DOCS ----------------
def search_all_documents(db: Session, query: str, file_ids: list[int], k: int = 6):
    query_embedding = embed_texts([query])[0]

    result = db.execute(
        text("""
            SELECT content, file_id
            FROM document_chunks
            WHERE file_id = ANY(:file_ids)
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :k
        """),
        {"file_ids": file_ids, "embedding": str(query_embedding), "k": k}
    )

    return [{"text": r[0], "file_id": r[1]} for r in result.fetchall()]


# ---------------- DELETE DOC ----------------
def delete_chunks(db: Session, file_id: int):
    db.execute(
        text("DELETE FROM document_chunks WHERE file_id = :file_id"),
        {"file_id": file_id}
    )
    db.commit()