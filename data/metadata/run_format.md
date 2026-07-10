# Retrieval Run Format

All retrieval results are saved as TSV files under `results/`.

## Header

run_name	query_id	page_id	rank	score

## Fields

- run_name: experiment name
- query_id: must match queries.jsonl
- page_id: must match corpus.jsonl and qrels.tsv
- rank: rank position starting from 1
- score: retrieval score, higher is better

## Constraints

- TSV with header
- one row per retrieved page
- no duplicate (query_id, page_id) within the same run
- unique rank per query
- scores sorted descending within each query
