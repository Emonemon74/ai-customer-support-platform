# Ingestion & retrieval benchmark

Machine: macOS-26.5.2-arm64-arm-64bit-Mach-O · arm · Python 3.14.0

Synthetic text PDFs (~2.8k characters per page), single process, embedded ChromaDB, embedding by Chroma's default ONNX MiniLM. Retrieval: 10 questions x 5 repeats per mode, top-5. LLM latency is excluded. Reproduce with `uv run python -m eval.benchmark`.

## Ingestion (parse -> chunk -> embed + index)

| Pages | PDF size | Chunks | Parse | Chunk | Embed + index | Total | Pages/s |
|---|---|---|---|---|---|---|---|
| 1 | 4 KB | 5 | 2 ms | 0 ms | 0.17 s | 0.17 s | 5.9 |
| 10 | 34 KB | 50 | 17 ms | 1 ms | 1.35 s | 1.37 s | 7.3 |
| 50 | 166 KB | 250 | 109 ms | 5 ms | 6.65 s | 6.76 s | 7.4 |
| 100 | 332 KB | 500 | 155 ms | 7 ms | 15.23 s | 15.39 s | 6.5 |
| 200 | 662 KB | 996 | 317 ms | 11 ms | 37.13 s | 37.45 s | 5.3 |

## Retrieval latency by index size (p50 / p95, ms)

| Pages | Chunks | vector | hybrid | hybrid + rerank |
|---|---|---|---|---|
| 1 | 5 | 74 / 81 | 74 / 86 | 146 / 154 |
| 10 | 50 | 76 / 86 | 78 / 92 | 370 / 435 |
| 50 | 250 | 76 / 88 | 85 / 91 | 370 / 435 |
| 100 | 500 | 83 / 103 | 95 / 112 | 409 / 518 |
| 200 | 996 | 87 / 92 | 123 / 151 | 490 / 765 |

## Needle check

A known billing-policy passage was hidden on page 101 of the 200-page PDF. The reranked top-5 returned it at rank **1**.
