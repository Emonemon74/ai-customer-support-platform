from app.ai.llm import generate_answer
from app.ai.retriever import retrieve_relevant_chunks


def build_context(question: str) -> str:
    chunks = retrieve_relevant_chunks(question)

    return "\n\n".join(chunks)


def ask_question(question: str) -> str:
    context = build_context(question)

    return generate_answer(
        question=question,
        context=context,
    )