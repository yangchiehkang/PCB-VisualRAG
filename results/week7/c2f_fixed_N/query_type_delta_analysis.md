# Week 7 Query Type Delta Analysis

Selected Budgeted MV run:

```text
results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
setting=low_cost N=20 M=8 compression=none
```

| Query Type | Query Count | BM25 nDCG@10 | BM25+Budgeted MV nDCG@10 | Delta nDCG@10 | BM25 Recall@10 | Budgeted Recall@10 | Delta Recall@10 | Conclusion |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| parameter_lookup | 2 | 0.6309 | 0.0000 | -0.6309 | 1.0000 | 0.0000 | -1.0000 | Harmed |
| structure_legend_interpretation | 5 | 0.6840 | 0.4152 | -0.2688 | 1.0000 | 0.8000 | -0.2000 | Harmed |
| component_localization | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | Unchanged |
| cross_page_consistency | 4 | 0.4171 | 0.0000 | -0.4171 | 0.6250 | 0.0000 | -0.6250 | Harmed |
| similarity_based_interference | 17 | 0.5514 | 0.1540 | -0.3973 | 1.0000 | 0.4118 | -0.5882 | Harmed |

## Key Findings

### Improved query types

- None

### Harmed query types

- parameter_lookup: Delta nDCG@10=-0.6309
- structure_legend_interpretation: Delta nDCG@10=-0.2688
- cross_page_consistency: Delta nDCG@10=-0.4171
- similarity_based_interference: Delta nDCG@10=-0.3973

### Unchanged query types

- component_localization: Delta nDCG@10=0.0000
