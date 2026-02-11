import chromadb
from chromadb.utils import embedding_functions

client=chromadb.Client()
embedding_function=embedding_functions.DefaultEmbeddingFunction()
collection=client.get_or_create_collection(name="documents",embedding_function=embedding_function)

def add_chunks(chunks,file_id):
    for i,chunk in enumerate(chunks):
        collection.add(documents=[chunk],ids=[f"{file_id}_{i}"])

def search_chunks(query, k=3):
    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    return results["documents"][0]
