import re
import unicodedata

from app.ai.hybrid_retriever import hybrid_search
from app.ai.llm import FALLBACK_ANSWER, generate_answer, stream_answer
from app.core.settings import settings


def _tag(filename: str | None, page) -> str:
    name = filename or "document"
    if page in (None, -1):
        return f"[{name}]"
    return f"[{name}, page {page}]"


# Models sometimes render the citation with fancy brackets (gpt-oss uses full-
# width 【 】) or non-breaking / narrow spaces. Fold all of that away before
# comparing the answer text to a source tag.
_BRACKETS = {"【": "[", "〔": "[", "「": "[",
             "】": "]", "〕": "]", "」": "]"}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for fancy, plain in _BRACKETS.items():
        text = text.replace(fancy, plain)
    return re.sub(r"\s+", " ", text).strip()


def reconcile_sources(answer: str, sources: list[dict]) -> list[dict]:
    """Keep the source list honest against the final answer.

    - If the model abstained it used none of the context, so return no sources.
    - Otherwise keep only sources the model actually cited by tag; if it cited
      nothing recognisable, fall back to the full retrieved list.
    """
    normalized = _normalize(answer)

    if normalized == _normalize(FALLBACK_ANSWER):
        return []

    cited = [
        s
        for s in sources
        if _normalize(_tag(s.get("filename"), s.get("page_number"))) in normalized
    ]
    return cited or sources


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
        f"{_tag(r['metadata'].get('filename'), r['metadata'].get('page_number'))}\n{r['text']}"
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

    return {"answer": answer, "sources": reconcile_sources(answer, sources)}


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

    yield from stream_answer(
        question=question,
        context=context,
        conversation_history=conversation_history,
    )
