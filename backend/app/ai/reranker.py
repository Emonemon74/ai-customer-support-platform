"""Cross-encoder reranking via FlashRank (ONNX runtime, no torch).

A bi-encoder (the dense vector search) scores the query and a chunk
independently; a cross-encoder reads them together and is much better at
telling a genuinely relevant passage from one that merely shares vocabulary.
We only run it over the small fused candidate pool, so the cost is bounded.

The model is downloaded on first use and cached on disk. If FlashRank or the
download is unavailable the module degrades to a no-op that preserves the
incoming order, so retrieval never hard-fails because of the reranker.
"""

import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

_ranker = None
_disabled = False


def _get_ranker():
    global _ranker, _disabled

    if _ranker is not None or _disabled:
        return _ranker

    try:
        from flashrank import Ranker

        _ranker = Ranker(model_name=settings.RERANKER_MODEL, cache_dir="/tmp/flashrank")
    except Exception:
        logger.exception("Reranker unavailable; falling back to fusion order")
        _disabled = True

    return _ranker


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    """``candidates`` are ``{"text", "metadata", "fused_score"}`` dicts.

    Returns them sorted by descending relevance with a ``rerank_score`` added.
    """
    if not candidates:
        return []

    ranker = _get_ranker()

    if ranker is None:
        for rank, item in enumerate(candidates):
            item["rerank_score"] = 1.0 / (rank + 1)
        return candidates

    from flashrank import RerankRequest

    passages = [
        {"id": i, "text": item["text"], "meta": {}}
        for i, item in enumerate(candidates)
    ]
    ranked = ranker.rerank(RerankRequest(query=query, passages=passages))

    out: list[dict] = []
    for entry in ranked:
        item = candidates[entry["id"]]
        item["rerank_score"] = float(entry["score"])
        out.append(item)

    return out
