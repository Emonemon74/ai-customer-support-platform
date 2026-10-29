"""Hybrid retrieval: dense vectors + BM25 keyword search, fused with
Reciprocal Rank Fusion, optionally reranked by a cross-encoder.

Everything is scoped to a single ``(user_id, conversation_id)`` pair. The BM25
index is built on demand from that conversation's chunks -- the corpora are
small (one user's uploads in one thread), so this stays cheap and always
reflects the latest documents without a separate index to maintain.
"""

import logging
import re

from app.ai.reranker import rerank
from app.ai.vector_store import collection
from app.core.settings import settings

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _scope(user_id: int, conversation_id: int) -> dict:
    return {
        "$and": [
            {"user_id": int(user_id)},
            {"conversation_id": int(conversation_id)},
        ]
    }


def _dense(question: str, where: dict, k: int) -> list[dict]:
    result = collection.query(query_texts=[question], n_results=k, where=where)

    ids = result["ids"][0]
    docs = result["documents"][0]
    metas = result["metadatas"][0]

    return [
        {"id": ids[i], "text": docs[i], "metadata": metas[i]}
        for i in range(len(ids))
    ]


def _bm25(question: str, where: dict, k: int) -> list[dict]:
    from rank_bm25 import BM25Okapi

    everything = collection.get(where=where)
    ids = everything["ids"]
    docs = everything["documents"]
    metas = everything["metadatas"]

    if not ids:
        return []

    bm25 = BM25Okapi([_tokenize(d) for d in docs])
    scores = bm25.get_scores(_tokenize(question))

    ranked = sorted(range(len(ids)), key=lambda i: scores[i], reverse=True)[:k]

    return [
        {"id": ids[i], "text": docs[i], "metadata": metas[i]}
        for i in ranked
        if scores[i] > 0
    ]


def _reciprocal_rank_fusion(*ranked_lists: list[dict]) -> list[dict]:
    rrf_k = settings.RETRIEVAL_RRF_K
    merged: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            entry = merged.setdefault(
                item["id"],
                {"text": item["text"], "metadata": item["metadata"], "fused_score": 0.0},
            )
            entry["fused_score"] += 1.0 / (rrf_k + rank + 1)

    return sorted(merged.values(), key=lambda e: e["fused_score"], reverse=True)


def hybrid_search(
    question: str,
    user_id: int,
    conversation_id: int,
    mode: str | None = None,
    top_n: int | None = None,
) -> list[dict]:
    user_id = int(user_id)
    conversation_id = int(conversation_id)

    if not user_id or not conversation_id:
        raise ValueError("retrieval requires both user_id and conversation_id")

    mode = mode or settings.RETRIEVAL_MODE
    top_n = top_n or settings.RETRIEVAL_TOP_N
    where = _scope(user_id, conversation_id)

    dense_hits = _dense(question, where, settings.RETRIEVAL_DENSE_K)

    if mode == "vector":
        results = [
            {**hit, "fused_score": 1.0 / (i + 1)}
            for i, hit in enumerate(dense_hits)
        ][:top_n]
        _log(question, conversation_id, mode, results)
        return results

    bm25_hits = _bm25(question, where, settings.RETRIEVAL_BM25_K)
    candidates = _reciprocal_rank_fusion(dense_hits, bm25_hits)

    if mode == "hybrid":
        results = candidates[:top_n]
        _log(question, conversation_id, mode, results)
        return results

    reranked = rerank(question, candidates[: settings.RETRIEVAL_DENSE_K])
    results = reranked[:top_n]
    _log(question, conversation_id, mode, results)
    return results


def _log(question: str, conversation_id: int, mode: str, results: list[dict]) -> None:
    logger.info(
        "retrieval mode=%s conversation=%s query=%r -> %s",
        mode,
        conversation_id,
        question[:80],
        [
            {
                "doc": r["metadata"].get("document_id"),
                "page": r["metadata"].get("page_number"),
                "chunk": r["metadata"].get("chunk_index"),
                "fused": round(r.get("fused_score", 0.0), 4),
                "rerank": round(r["rerank_score"], 4) if "rerank_score" in r else None,
            }
            for r in results
        ],
    )
