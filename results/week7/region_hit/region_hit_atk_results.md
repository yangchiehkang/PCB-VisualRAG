# Week 7 Day 5 Region Hit@k Results

## Table 10: Region Hit@k 结果表

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 | Status |
|---|---:|---:|---:|---|
| Full MV | 0.0000 | 0.0000 | 0.0000 | PASSED |
| Budgeted MV | 0.0000 | 0.0000 | 0.1000 | PASSED |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.2000 | PASSED |
| Hybrid Fusion | 0.0000 | 0.2000 | 0.4000 | PASSED |

## Settings

- Patch grid: 7x7
- Patch ranking: automatic edge-density saliency
- Center-inside-bbox: enabled
- IoU threshold: 0.3
- Region hit rule: center hit OR IoU hit
- k values: 1, 3, 5