from app.ai.embeddings import generate_embeddings
from app.ai.vector_store import collection


def retrieve_relevant_chunks(question: str, n_results: int = 3):
    query_embedding = generate_embeddings([question])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    return documents, metadatas