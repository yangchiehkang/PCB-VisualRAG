# Week 7 BM25-C2F All Configs Results

| Method | Setting | N | M | Compression | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| BM25 | baseline | - | - | - | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | - |
| BM25 + Full MV Rerank | fullmv_N10 | 10 | - | none | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 9.361923 |
| BM25 + Full MV Rerank | fullmv_N20 | 20 | - | none | 0.0667 | 0.1667 | 0.3333 | 0.1211 | 0.1691 | 13.855763 |
| BM25 + Full MV Rerank | fullmv_N50 | 50 | - | none | 0.0667 | 0.1000 | 0.1333 | 0.0881 | 0.0988 | 32.776340 |
| BM25 + Full MV Rerank | fullmv_N100 | 100 | - | none | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 | 63.873790 |
| BM25 + Budgeted MV Rerank | low_cost | 20 | 8 | none | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 12.674273 |
| BM25 + Budgeted MV Rerank | mid_cost | 20 | 16 | none | 0.0000 | 0.1667 | 0.3667 | 0.0843 | 0.1490 | 12.856343 |
| BM25 + Budgeted MV Rerank | higher_quality | 50 | 24 | none | 0.0000 | 0.0333 | 0.1000 | 0.0170 | 0.0359 | 31.910323 |
