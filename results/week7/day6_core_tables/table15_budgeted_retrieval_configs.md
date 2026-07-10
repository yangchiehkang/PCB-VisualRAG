# Week 7 Day 6 Table 15: Budgeted Retrieval 代表配置表

## Table 15: Budgeted Retrieval 代表配置表

| Config | N | M | Compression | nDCG@10 | Index Size MB | Latency |
|---|---:|---:|---|---:|---:|---:|
| Full MV | full | 49 | None | 0.3628 | 0.01 | 9.3619 |
| Budgeted Low-cost | 20 | 8 | PQ | 0.1565 | 0.02 | 12.6743 |
| Budgeted Mid-cost | 20 | 16 | PQ | 0.1490 | 0.02 | 12.8563 |
| Budgeted High-quality | 50 | 24 | PQ | 0.0359 | 0.02 | 31.9103 |

## Source Files

| Config | Source File |
|---|---|
| Full MV | results\week7\c2f_fixed_N\bm25_c2f_all_configs_results.csv |
| Budgeted Low-cost | results\week7\c2f_fixed_N\bm25_c2f_all_configs_results.csv |
| Budgeted Mid-cost | results\week7\c2f_fixed_N\bm25_c2f_all_configs_results.csv |
| Budgeted High-quality | results\week7\c2f_fixed_N\bm25_c2f_all_configs_results.csv |