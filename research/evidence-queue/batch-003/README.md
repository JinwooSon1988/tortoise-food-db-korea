# Batch 003 work queue (checkpoint)

- `queue_results.jsonl.gz`: one line per catalog species searched in Europe PMC with land-tortoise terms (query, hit count,
  up to 25 hits). 18,283 of the 22,565 queued species were processed; the host stopped the process when the computer ran
  low on memory. 0 failed after retries, 42 retries.
- `mentions.jsonl.gz`: for every open-access hit, where the species name occurs in the full text (sentence or table row,
  with flags). These are search results, not evidence; only records read and accepted by hand are in
  `data/catalog-evidence/batch-003-20261022.json`.
- `queue_log.txt`: progress log. `make_stats.json`: counts printed by `make_batch_003.py`.

## Resume the queue (4,282 species left)

```
mkdir q && gunzip -c research/evidence-queue/batch-003/queue_results.jsonl.gz > q/queue_results.jsonl
python -X utf8 scripts/evidence_corpus/batch_003/epmc_queue.py data/plant-catalog/search.json q
python -X utf8 scripts/evidence_corpus/batch_003/mentions.py q/queue_results.jsonl q/xml <cached xml dir> q/mentions.jsonl
python -X utf8 scripts/evidence_corpus/batch_003/review_view.py q/mentions.jsonl > q/review.txt
```

`epmc_queue.py` skips species already in `queue_results.jsonl` and adapts its concurrency (halves on HTTP 429/5xx).
