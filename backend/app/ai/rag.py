from app.ai.hybrid_retriever import hybrid_search
from app.ai.llm import generate_answer, stream_answer
from app.core.settings import settings


def _is_relevant(result: dict) -> bool:
    if "rerank_score" in result:
        return result["rerank_score"] >= settings.RETRIEVAL_MIN_SCORE
    return True


def _format_sources(results: list[dict]) -> list[dict]:
    """One entry per (document, page), in the order first seen."""
    sources: list[dict] = []
    seen: set[tuple] = set()

    for result in results:
        meta = result["metadata"]
        page = meta.get("page_number")
        page = None if page in (None, -1) else page
        key = (meta.get("document_id"), page)

        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "document_id": meta.get("document_id"),
                "conversation_id": meta.get("conversation_id"),
                "chunk_index": meta.get("chunk_index"),
                "filename": meta.get("filename"),
                "page_number": page,
            }
        )

    return sources


def build_context(question: str, user_id: int, conversation_id: int):
    results = hybrid_search(
        question=question,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    relevant = [r for r in results if _is_relevant(r)]

    # Nothing cleared the relevance bar -> hand the model no context so it
    # takes the "not found in your documents" path instead of guessing.
    if not relevant:
        return "", []

    context = "\n\n".join(
        f"[{r['metadata'].get('filename', 'document')}"
        + (
            f", page {r['metadata']['page_number']}"
            if r["metadata"].get("page_number", -1) not in (None, -1)
            else ""
        )
        + f"]\n{r['text']}"
        for r in relevant
    )

    return context, _format_sources(relevant)


def ask_question(
    question: str,
    user_id: int,
    conversation_id: int,
    conversation_history: str = "",
):
    context, sources = build_context(
        question=question,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    answer = generate_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    )

    return {"answer": answer, "sources": sources}


def stream_question(
    question: str,
    user_id: int,
    conversation_id: int,
    conversation_history: str = "",
):
    context, _sources = build_context(
        question=question,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    for token in stream_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    ):
        yield token
