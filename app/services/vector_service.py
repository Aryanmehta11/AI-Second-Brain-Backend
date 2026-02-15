import chromadb
import os
print("Current working directory:", os.getcwd())
from chromadb.utils import embedding_functions


client = chromadb.PersistentClient(path="./chroma_db")

embedding_function = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_function
)


# ---------------- ADD DOCUMENT CHUNKS ----------------
def add_chunks(chunks: list[str], file_id: int):
    ids = []
    metadatas = []
    file_id=str(file_id)  # 🔥 critical: convert to string

    for i, chunk in enumerate(chunks):
        ids.append(f"{file_id}_{i}")
        metadatas.append({"file_id": file_id})

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )

    


# ---------------- SEARCH DOCUMENT ----------------
def search_chunks(query: str, file_id: int, k: int = 4):
    file_id = str(file_id) 
    results = collection.query(
        query_texts=[query],
        n_results=k,
        where={"file_id": file_id}  # 🔥 critical
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    return results["documents"][0]
