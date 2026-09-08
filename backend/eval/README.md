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
uv run python -m eval.run_eval          # ingest, evaluate, write results.md, clean up
uv run python -m eval.run_eval --keep   # leave the eval data in the vector store
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
- **Abstain@unanswerable** – fraction of unanswerable questions where every
  candidate fell below `RETRIEVAL_MIN_SCORE`, so `build_context` returns no
  context and the model must say the answer isn't in the documents. Only the
  `rerank` mode produces a score to threshold on.
- **p50 latency** – median retrieval time per query on this machine.

## Latest results

See [`results.md`](results.md). Summary on the bundled 6-document corpus:
hybrid closes a keyword-match gap in Recall@3 (0.97 → 1.00), reranking lifts MRR
(0.95 → 0.99) by ordering the correct passage first, and the relevance
threshold (`RETRIEVAL_MIN_SCORE`, default 0.15) lets the system decline
unanswerable questions that the score-free modes always answer — at roughly 3x
the retrieval latency. Raising the threshold trades recall for a higher
abstention rate.

The corpus is small, so Recall@5 saturates; run it against a larger real
document set to see the modes separate further.
