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




# ---------------- HYBRID SEARCH SINGLE DOC ----------------
def hybrid_search_chunks(db: Session, query: str, file_id: int, k: int = 4):
    query_embedding = embed_texts([query])[0]

    result = db.execute(
        text("""
            WITH vector_search AS (
                SELECT 
                    content,
                    ROW_NUMBER() OVER (
                        ORDER BY embedding <=> CAST(:embedding AS vector)
                    ) as rank
                FROM document_chunks
                WHERE file_id = :file_id
            ),
            keyword_search AS (
                SELECT 
                    content,
                    ROW_NUMBER() OVER (
                        ORDER BY ts_rank(content_tsv, plainto_tsquery('english', :query)) DESC
                    ) as rank
                FROM document_chunks
                WHERE file_id = :file_id
                AND content_tsv @@ plainto_tsquery('english', :query)
            ),
            rrf_scores AS (
                SELECT 
                    content,
                    SUM(1.0 / (60 + rank)) as rrf_score
                FROM (
                    SELECT content, rank FROM vector_search
                    UNION ALL
                    SELECT content, rank FROM keyword_search
                ) combined
                GROUP BY content
            )
            SELECT content
            FROM rrf_scores
            ORDER BY rrf_score DESC
            LIMIT :k
        """),
        {
            "file_id": file_id,
            "embedding": str(query_embedding),
            "query": query,
            "k": k
        }
    )

    return [row[0] for row in result.fetchall()]
# ---------------- DELETE DOC ----------------
def delete_chunks(db: Session, file_id: int):
    db.execute(
        text("DELETE FROM document_chunks WHERE file_id = :file_id"),
        {"file_id": file_id}
    )
    db.commit()

# ---------------- HYBRID SEARCH ALL DOCS ----------------
def hybrid_search_all_documents(db: Session, query: str, file_ids: list[int], k: int = 6):
    query_embedding = embed_texts([query])[0]

    result = db.execute(
        text("""
            WITH vector_search AS (
                SELECT
                    content,
                    file_id,
                    ROW_NUMBER() OVER (
                        ORDER BY embedding <=> CAST(:embedding AS vector)
                    ) as rank
                FROM document_chunks
                WHERE file_id = ANY(:file_ids)
            ),
            keyword_search AS (
                SELECT
                    content,
                    file_id,
                    ROW_NUMBER() OVER (
                        ORDER BY ts_rank(content_tsv, plainto_tsquery('english', :query)) DESC
                    ) as rank
                FROM document_chunks
                WHERE file_id = ANY(:file_ids)
                AND content_tsv @@ plainto_tsquery('english', :query)
            ),
            rrf_scores AS (
                SELECT
                    content,
                    file_id,
                    SUM(1.0 / (60 + rank)) as rrf_score
                FROM (
                    SELECT content, file_id, rank FROM vector_search
                    UNION ALL
                    SELECT content, file_id, rank FROM keyword_search
                ) combined
                GROUP BY content, file_id
            )
            SELECT content, file_id
            FROM rrf_scores
            ORDER BY rrf_score DESC
            LIMIT :k
        """),
        {
            "file_ids": file_ids,
            "embedding": str(query_embedding),
            "query": query,
            "k": k
        }
    )

    return [{"text": r[0], "file_id": r[1]} for r in result.fetchall()]    