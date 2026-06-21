from app.ai.llm import generate_answer, stream_answer
from app.ai.retriever import retrieve_relevant_chunks


def build_context(question: str):
    chunks, metadatas = retrieve_relevant_chunks(question)

    context = "\n\n".join(chunks)

    return context, metadatas


def ask_question(
    question: str,
    conversation_history: str = "",
):
    context, sources = build_context(question)

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
    conversation_history: str = "",
):
    context, _sources = build_context(question)

    for token in stream_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    ):
        yield token