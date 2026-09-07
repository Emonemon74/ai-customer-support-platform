"""Retrieval evaluation harness.

Ingests the text corpus in ``eval/corpus`` into the vector store under a
reserved sentinel user/conversation, then measures three retrieval modes
against ``eval/dataset.jsonl``:

    vector  -> dense similarity only (baseline)
    hybrid  -> dense + BM25 fused with RRF
    rerank  -> hybrid candidates re-scored by the cross-encoder

Metrics
-------
Recall@5         fraction of answerable questions whose correct (document, page)
                 chunk appears in the top 5
Doc Recall@5     same but only the document has to match
MRR             mean reciprocal rank of the first fully-correct chunk
Abstain@unans   fraction of unanswerable questions where the relevance
                 threshold left no context (so the model must say "not found")
p50 latency     median retrieval time per query

Usage:  uv run python -m eval.run_eval [--keep]
"""

import argparse
import json
import pathlib
import statistics
import time

from app.ai.chunker import TextChunker
from app.ai.hybrid_retriever import hybrid_search
from app.ai.vector_store import VectorStore, collection
from app.core.settings import settings

EVAL_USER_ID = 999_000_001
EVAL_CONVERSATION_ID = 999_000_002

HERE = pathlib.Path(__file__).parent
CORPUS_DIR = HERE / "corpus"
DATASET = HERE / "dataset.jsonl"
RESULTS = HERE / "results.md"

MODES = ["vector", "hybrid", "rerank"]


def _pages(raw: str) -> list[dict]:
    preamble, _, rest = raw.partition("---PAGE---")
    parts = [p.strip() for p in rest.split("---PAGE---") if p.strip()]
    if parts:
        parts[0] = f"{preamble.strip()}\n\n{parts[0]}".strip()
    return [{"page_number": i + 1, "text": text} for i, text in enumerate(parts)]


def ingest() -> dict[int, str]:
    _cleanup()
    filenames: dict[int, str] = {}

    for doc_id, path in enumerate(sorted(CORPUS_DIR.glob("*.txt")), start=1):
        pages = _pages(path.read_text())
        chunks = TextChunker.chunk_pages(pages)
        VectorStore().add_document(
            document_id=doc_id,
            chunks=chunks,
            user_id=EVAL_USER_ID,
            conversation_id=EVAL_CONVERSATION_ID,
            filename=path.name,
        )
        filenames[doc_id] = path.name
        print(f"  ingested {path.name}: {len(pages)} pages -> {len(chunks)} chunks")

    return filenames


def _cleanup() -> None:
    ids = collection.get(where={"user_id": EVAL_USER_ID})["ids"]
    if ids:
        collection.delete(ids=ids)


def load_dataset() -> list[dict]:
    return [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]


def _first_correct_rank(results: list[dict], row: dict) -> int | None:
    for position, result in enumerate(results, start=1):
        meta = result["metadata"]
        if (
            meta.get("filename") == row["expected_doc"]
            and meta.get("page_number") == row["expected_page"]
        ):
            return position
    return None


def evaluate(mode: str, dataset: list[dict]) -> dict:
    hits_at_3 = 0
    hits_at_5 = 0
    doc_hits = 0
    reciprocal_ranks: list[float] = []
    answerable = 0
    abstain_hits = 0
    unanswerable = 0
    latencies: list[float] = []

    for row in dataset:
        start = time.perf_counter()
        results = hybrid_search(
            question=row["question"],
            user_id=EVAL_USER_ID,
            conversation_id=EVAL_CONVERSATION_ID,
            mode=mode,
            top_n=5,
        )
        latencies.append((time.perf_counter() - start) * 1000)

        if row["expected_doc"] is None:
            unanswerable += 1
            relevant = [
                r for r in results
                if r.get("rerank_score", 1.0) >= settings.RETRIEVAL_MIN_SCORE
            ]
            if not relevant:
                abstain_hits += 1
            continue

        answerable += 1

        if any(r["metadata"].get("filename") == row["expected_doc"] for r in results):
            doc_hits += 1

        rank = _first_correct_rank(results, row)
        if rank is not None and rank <= 3:
            hits_at_3 += 1
        if rank is not None and rank <= 5:
            hits_at_5 += 1
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

    return {
        "recall_at_3": hits_at_3 / answerable if answerable else 0.0,
        "recall_at_5": hits_at_5 / answerable if answerable else 0.0,
        "doc_recall_at_5": doc_hits / answerable if answerable else 0.0,
        "mrr": statistics.mean(reciprocal_ranks) if reciprocal_ranks else 0.0,
        "abstain_rate": abstain_hits / unanswerable if unanswerable else 0.0,
        "p50_latency_ms": statistics.median(latencies),
        "mean_latency_ms": statistics.mean(latencies),
    }


def render(rows: dict[str, dict]) -> str:
    header = (
        "| Mode | Recall@3 | Recall@5 | Doc Recall@5 | MRR | Abstain@unanswerable | p50 latency (ms) |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    body = ""
    labels = {"vector": "vector-only (baseline)", "hybrid": "+ hybrid (BM25)", "rerank": "+ hybrid + rerank"}
    for mode in MODES:
        m = rows[mode]
        body += (
            f"| {labels[mode]} | {m['recall_at_3']:.2f} | {m['recall_at_5']:.2f} "
            f"| {m['doc_recall_at_5']:.2f} | {m['mrr']:.3f} | {m['abstain_rate']:.2f} "
            f"| {m['p50_latency_ms']:.0f} |\n"
        )
    return header + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="don't delete eval data afterwards")
    args = parser.parse_args()

    print(f"Reranker model: {settings.RERANKER_MODEL}")
    print("Ingesting corpus...")
    ingest()

    dataset = load_dataset()
    print(f"Running {len(dataset)} questions across {len(MODES)} modes...\n")

    rows = {mode: evaluate(mode, dataset) for mode in MODES}
    table = render(rows)

    print(table)

    RESULTS.write_text(
        "# Retrieval evaluation results\n\n"
        f"Corpus: {len(list(CORPUS_DIR.glob('*.txt')))} documents. "
        f"Questions: {len(dataset)} "
        f"({sum(1 for r in dataset if r['expected_doc'] is None)} unanswerable).\n\n"
        f"Reranker: `{settings.RERANKER_MODEL}`.\n\n"
        + table
        + "\nGenerated by `uv run python -m eval.run_eval`.\n"
    )
    print(f"Wrote {RESULTS.relative_to(HERE.parent)}")

    if not args.keep:
        _cleanup()
        print("Cleaned up eval data from the vector store.")


if __name__ == "__main__":
    main()
