"""Ingestion and retrieval benchmark.

Generates synthetic PDFs of increasing length and times each ingestion stage
(parse -> chunk -> embed + index) plus retrieval latency per mode against the
resulting index. The LLM is deliberately excluded: its latency depends on the
provider, not on this code, and is already logged per request in production.

The needle check hides a known passage from the eval corpus inside the largest
PDF and verifies the right (document, page) is still found, so a latency win is
never bought with a recall loss.

Usage:  uv run python -m eval.benchmark [--pages 1 10 50 100 200] [--repeats 5]
"""

import argparse
import json
import pathlib
import platform
import random
import statistics
import tempfile
import time

from app.ai.chunker import TextChunker
from app.ai.hybrid_retriever import hybrid_search
from app.ai.parser import PDFParser
from app.ai.vector_store import VectorStore, collection

BENCH_USER_ID = 999_000_101
CONVERSATION_BASE = 999_100_000

HERE = pathlib.Path(__file__).parent
RESULTS = HERE / "benchmark_results.md"
MODES = ["vector", "hybrid", "rerank"]

# Filler vocabulary is unrelated to the eval corpus so it cannot be mistaken
# for the needle passage.
_VOCAB = (
    "harbor lantern quarry meadow copper willow anchor glacier ribbon thunder "
    "marble orchard falcon canyon velvet compass ember tundra saddle pebble "
    "mirror cedar lagoon beacon thistle granite ferry cobalt hollow juniper "
    "monsoon pylon satchel trellis walnut zephyr bramble cinder dune fjord "
    "gable ivory kelp lichen mosaic nectar obsidian parcel quartz raven "
    "sorrel tarn umber vesper wicker yarrow"
).split()


def _filler_page(rng: random.Random, chars: int = 2800) -> str:
    sentences = []
    while sum(len(s) for s in sentences) < chars:
        words = [rng.choice(_VOCAB) for _ in range(rng.randint(9, 16))]
        sentences.append(" ".join(words).capitalize() + ".")
    return " ".join(sentences)


def _wrap(text: str, width: int = 92) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def _escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list[str]) -> bytes:
    """Minimal text-only PDF (Helvetica, one content stream per page)."""
    objects: list[bytes] = []
    n = len(pages)
    page_ids = [3 + i * 2 for i in range(n)]

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())

    font_id = 3 + n * 2
    for i, text in enumerate(pages):
        content_id = page_ids[i] + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_id} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ).encode()
        )
        ops = ["BT", "/F1 10 Tf", "13 TL", "50 750 Td"]
        for line in _wrap(text):
            ops.append(f"({_escape(line)}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1", "replace")
        objects.append(
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


def _pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def _needle() -> tuple[str, str]:
    """A known passage + question from the eval set, to hide in the haystack."""
    from eval.run_eval import _pages

    dataset = [
        json.loads(line)
        for line in (HERE / "dataset.jsonl").read_text().splitlines()
        if line.strip()
    ]
    row = next(
        r
        for r in dataset
        if r["expected_doc"] == "billing_policy.txt" and r["expected_page"] == 2
    )
    pages = _pages((HERE / "corpus" / "billing_policy.txt").read_text())
    return pages[row["expected_page"] - 1]["text"], row["question"]


def run(sizes: list[int], repeats: int) -> tuple[list[dict], dict]:
    questions = [
        json.loads(line)["question"]
        for line in (HERE / "dataset.jsonl").read_text().splitlines()
        if line.strip() and json.loads(line)["expected_doc"]
    ][:10]
    needle_text, needle_question = _needle()
    rng = random.Random(7)
    rows: list[dict] = []
    needle_result: dict = {}

    # Warm the embedding model and rerank model so first-call load time does
    # not pollute the smallest size.
    warm = CONVERSATION_BASE - 1
    VectorStore().add_document(0, [{"text": "warm up", "page_number": 1, "chunk_index": 0}], BENCH_USER_ID, warm, "warm.pdf")
    hybrid_search("warm up", BENCH_USER_ID, warm, mode="rerank", top_n=5)

    with tempfile.TemporaryDirectory() as tmp:
        for index, size in enumerate(sizes):
            conversation_id = CONVERSATION_BASE + index
            pages = [_filler_page(rng) for _ in range(size)]
            needle_page = size // 2
            if index == len(sizes) - 1:
                pages[needle_page] = needle_text
            pdf = build_pdf(pages)
            path = pathlib.Path(tmp) / f"bench_{size}.pdf"
            path.write_bytes(pdf)

            t0 = time.perf_counter()
            parsed = PDFParser.extract_pages(str(path))
            t1 = time.perf_counter()
            chunks = TextChunker.chunk_pages(parsed)
            t2 = time.perf_counter()
            VectorStore().add_document(
                document_id=index + 1,
                chunks=chunks,
                user_id=BENCH_USER_ID,
                conversation_id=conversation_id,
                filename=path.name,
            )
            t3 = time.perf_counter()

            row = {
                "pages": size,
                "pdf_kb": len(pdf) / 1024,
                "chunks": len(chunks),
                "parse_ms": (t1 - t0) * 1000,
                "chunk_ms": (t2 - t1) * 1000,
                "index_ms": (t3 - t2) * 1000,
                "total_ms": (t3 - t0) * 1000,
            }

            for mode in MODES:
                samples = []
                for _ in range(repeats):
                    for question in questions:
                        start = time.perf_counter()
                        hybrid_search(question, BENCH_USER_ID, conversation_id, mode=mode, top_n=5)
                        samples.append((time.perf_counter() - start) * 1000)
                row[f"{mode}_p50"] = statistics.median(samples)
                row[f"{mode}_p95"] = _pct(samples, 0.95)

            rows.append(row)
            print(
                f"  {size:>4} pages | {row['chunks']:>5} chunks | "
                f"ingest {row['total_ms'] / 1000:6.2f}s | "
                f"rerank p50 {row['rerank_p50']:6.0f} ms"
            )

            if index == len(sizes) - 1:
                results = hybrid_search(
                    needle_question, BENCH_USER_ID, conversation_id, mode="rerank", top_n=5
                )
                rank = next(
                    (
                        i
                        for i, r in enumerate(results, start=1)
                        if r["metadata"].get("page_number") == needle_page + 1
                    ),
                    None,
                )
                needle_result = {
                    "pages": size,
                    "needle_page": needle_page + 1,
                    "rank": rank,
                }

    return rows, needle_result


def cleanup() -> None:
    ids = collection.get(where={"user_id": BENCH_USER_ID})["ids"]
    if ids:
        collection.delete(ids=ids)


def render(rows: list[dict], needle: dict, repeats: int) -> str:
    out = [
        "# Ingestion & retrieval benchmark\n",
        f"Machine: {platform.platform()} · {platform.processor() or platform.machine()} · "
        f"Python {platform.python_version()}\n",
        "Synthetic text PDFs (~2.8k characters per page), single process, "
        "embedded ChromaDB, embedding by Chroma's default ONNX MiniLM. "
        f"Retrieval: 10 questions x {repeats} repeats per mode, top-5. "
        "LLM latency is excluded. Reproduce with `uv run python -m eval.benchmark`.\n",
        "## Ingestion (parse -> chunk -> embed + index)\n",
        "| Pages | PDF size | Chunks | Parse | Chunk | Embed + index | Total | Pages/s |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['pages']} | {r['pdf_kb']:.0f} KB | {r['chunks']} "
            f"| {r['parse_ms']:.0f} ms | {r['chunk_ms']:.0f} ms | {r['index_ms'] / 1000:.2f} s "
            f"| {r['total_ms'] / 1000:.2f} s | {r['pages'] / (r['total_ms'] / 1000):.1f} |"
        )
    out += [
        "\n## Retrieval latency by index size (p50 / p95, ms)\n",
        "| Pages | Chunks | vector | hybrid | hybrid + rerank |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        cells = " | ".join(f"{r[f'{m}_p50']:.0f} / {r[f'{m}_p95']:.0f}" for m in MODES)
        out.append(f"| {r['pages']} | {r['chunks']} | {cells} |")
    if needle:
        out += [
            "\n## Needle check\n",
            f"A known billing-policy passage was hidden on page {needle['needle_page']} of the "
            f"{needle['pages']}-page PDF. The reranked top-5 returned it at rank "
            f"**{needle['rank'] if needle['rank'] else 'not found'}**.",
        ]
    return "\n".join(out) + "\n"


def main() -> None:
    import logging

    logging.disable(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, nargs="+", default=[1, 10, 50, 100, 200])
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    cleanup()
    try:
        print("Benchmarking...")
        rows, needle = run(args.pages, args.repeats)
    finally:
        cleanup()

    report = render(rows, needle, args.repeats)
    RESULTS.write_text(report)
    print(f"\nWrote {RESULTS}")
    print(report)


if __name__ == "__main__":
    main()
