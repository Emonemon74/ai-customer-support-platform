"""Backwards-compatible thin wrapper around the hybrid retriever."""

from app.ai.hybrid_retriever import hybrid_search


def retrieve_relevant_chunks(
    question: str,
    user_id: int,
    conversation_id: int,
    n_results: int = 3,
):
    results = hybrid_search(
        question=question,
        user_id=user_id,
        conversation_id=conversation_id,
        top_n=n_results,
    )

    documents = [r["text"] for r in results]
    metadatas = [r["metadata"] for r in results]

    return documents, metadatas
