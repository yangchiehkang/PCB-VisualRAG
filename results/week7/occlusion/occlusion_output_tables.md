# Week 7 Day 5 Occlusion Output Tables

## Table 12: Occlusion 对照结果表

| Condition | Recall@10 | MRR@10 | nDCG@10 | Avg Gold Page Score |
|---|---:|---:|---:|---:|
| Original | 1.0000 | 1.0000 | 1.0000 | 0.20149380 |
| Gold Mask | 0.0000 | 0.0000 | 0.0000 | 0.00000000 |
| Random Mask | 1.0000 | 1.0000 | 1.0000 | 0.20149380 |

## Table 13: Counterfactual Occlusion Gap 表

| Metric | Random Mask | Gold Mask | COG |
|---|---:|---:|---:|
| Recall@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| MRR@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| nDCG@10 | 1.00000000 | 0.00000000 | 1.00000000 |
| Gold Page Score | 0.20149380 | 0.00000000 | 0.20149380 |

## Source

```text
results\week7\occlusion\occlusion_metrics_per_query.csv
```