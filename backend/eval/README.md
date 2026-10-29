# Retrieval evaluation

A reproducible benchmark for the retrieval pipeline. It measures three modes on
a fixed question set so changes can be judged by numbers, not by asking a few
questions by hand.

## Modes

| Mode | What it does |
|---|---|
| `vector` | dense similarity search only (the original behaviour) |
| `hybrid` | dense + BM25 keyword search, fused with Reciprocal Rank Fusion |
| `rerank` | hybrid candidates re-scored by a `ms-marco-MiniLM` cross-encoder, then a relevance threshold |

## Running it

```bash
cd backend
uv run python -m eval.run_eval                 # retrieval metrics only
uv run python -m eval.run_eval --with-answers  # + LLM answer-quality pass (one Groq call per question)
uv run python -m eval.run_eval --keep          # leave the eval data in the vector store
```

The corpus (`corpus/*.txt`, split into pages with `---PAGE---` markers) is
ingested under a reserved sentinel user/conversation id so it never collides
with real data, and removed again at the end.

## Metrics

- **Recall@k** – fraction of answerable questions whose exact `(document, page)`
  chunk is in the top k.
- **Doc Recall@5** – looser: any chunk from the right document is in the top 5.
- **MRR** – mean reciprocal rank of the first fully-correct chunk. Rewards
  putting the right passage *first*, which is what the reranker is for.
- **p50 latency** – median retrieval time per query on this machine.

Abstention is measured at the answer layer, not retrieval: `--with-answers`
reports **correct abstention** on unanswerable questions and **over-abstention**
on answerable ones. `build_context` withholds context only when retrieval is
empty; otherwise the grounding prompt decides.

## Latest results

See [`results.md`](results.md). Summary on the bundled 6-document corpus:
hybrid closes a keyword-match gap in Recall@3 (0.97 → 1.00), reranking lifts MRR
(0.95 → 0.99) by ordering the correct passage first — at roughly 3x the
retrieval latency. With the grounding prompt doing the abstaining, the `rerank`
pipeline scores 1.00 correct abstention on unanswerable questions and 0.00
over-abstention on answerable ones.

The corpus is small, so Recall@5 saturates; run it against a larger real
document set to see the modes separate further.

`--with-answers` grades the production (rerank) pipeline end to end with the
LLM: **source accuracy ~0.97** (the answer cited the expected document + page),
**correct abstention 1.00** on the 7 unanswerable questions, over-abstention
~0.03. Answer accuracy (~0.76) is a strict substring check against a short
expected string, so it undercounts correct answers that paraphrase ("twenty
nine" vs "29") — treat it as a floor.

## Ingestion & retrieval benchmark

`eval/benchmark.py` times ingestion (parse, chunk, embed + index) and retrieval
latency per mode on synthetic PDFs of 1–200 pages, and hides a known passage in
the largest one as a recall check. It excludes the LLM.

```bash
uv run python -m eval.benchmark [--pages 1 10 50 100 200] [--repeats 5]
```

Results are written to [`benchmark_results.md`](benchmark_results.md). Run only
one instance at a time: runs share the vector store and sentinel ids.
