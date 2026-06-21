from app.ai.llm import generate_answer, stream_answer
from app.ai.retriever import retrieve_relevant_chunks


def build_context(question: str, user_id: int):
    chunks, metadatas = retrieve_relevant_chunks(
        question=question,
        user_id=user_id,
    )

    context = "\n\n".join(chunks)

    return context, metadatas


def ask_question(
    question: str,
    user_id: int,
    conversation_history: str = "",
):
    context, sources = build_context(
        question=question,
        user_id=user_id,
    )

    answer = generate_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    )

    return {
        "answer": answer,
        "sources": sources,
    }


def stream_question(
    question: str,
    user_id: int,
    conversation_history: str = "",
):
    context, sources = build_context(
        question=question,
        user_id=user_id,
    )

    for token in stream_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    ):
        yield token