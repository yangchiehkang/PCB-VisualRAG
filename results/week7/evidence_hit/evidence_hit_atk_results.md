# Week 7 Day 5 Evidence Hit@k Results

## Table 9: Evidence Hit@k 结果表

| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 | Status | Run File |
|---|---:|---:|---:|---|---|
| BM25 | 0.4000 | 1.0000 | 1.0000 | PASSED | results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv |
| Single-vector Visual | - | - | - | MISSING_RUN | - |
| Full MV | 0.1000 | 0.4000 | 1.0000 | PASSED | results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv |
| Budgeted MV | 0.1000 | 0.2000 | 0.4000 | PASSED | results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv |
| BM25 + Budgeted MV | 0.1000 | 0.2000 | 0.4000 | PASSED | results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv |
| Hybrid Fusion | 0.4000 | 1.0000 | 1.0000 | PASSED | results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv |

## Definition

For each query, page-level evidence hit checks whether the gold evidence page appears in top-k retrieved pages.

```text
EvidenceHit@k(q) = 1 if g(q) is in R_k(q), else 0
EvidenceHitRate@k = average over selected evidence queries
```