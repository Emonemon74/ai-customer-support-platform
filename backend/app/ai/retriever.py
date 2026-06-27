from app.ai.vector_store import collection


def retrieve_relevant_chunks(
    question: str,
    user_id: int,
    conversation_id: int,
    n_results: int = 3,
):
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where={
            "$and": [
                {"user_id": user_id},
                {"conversation_id": conversation_id},
            ],
        },
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    return documents, metadatas
