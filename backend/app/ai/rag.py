from app.ai.llm import generate_answer
from app.ai.retriever import retrieve_relevant_chunks


def build_context(question: str):
    chunks, metadatas = retrieve_relevant_chunks(question)

    context = "\n\n".join(chunks)

    return context, metadatas


def ask_question(question: str):
    context, sources = build_context(question)

    answer = generate_answer(
        question=question,
        context=context,
    )

    return {
        "answer": answer,
        "sources": sources,
    }