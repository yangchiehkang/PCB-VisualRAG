# Week 7 BM25-C2F Main Results

| Method | Setting | N | M | Compression | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| BM25 | baseline | - | - | - | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | - |
| BM25 + Full MV Rerank | fullmv_N10 | 10 | - | none | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 9.361923 |
| BM25 + Budgeted MV Rerank | low_cost | 20 | 8 | none | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 12.674273 |
