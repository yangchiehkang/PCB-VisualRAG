# Day 3 Dense Text Baseline Summary

## Outputs
- results/dense_text_run.tsv
- results/dense_text_metrics.json

## Overall Metrics
| Metric | BM25 | Dense Text |
|---|---:|---:|
| Recall@1 | 0.1333 | 0.1000 |
| Recall@3 | 0.6833 | 0.4500 |
| Recall@5 | 0.6833 | 0.6000 |
| Recall@10 | 0.8833 | 0.8000 |
| nDCG@10 | 0.5241 | 0.4420 |
| MRR | 0.4105 | 0.3358 |

## Key Findings
- Dense text retrieval did not outperform BM25 overall on OCR page retrieval.
- BM25 remained stronger on overall recall and ranking quality.
- Dense retrieval showed slightly better top-1 behavior on similarity-based interference queries.
- Component localization remained difficult for both text-only baselines.
- The results suggest that OCR text alone is insufficient for visually grounded page retrieval.

## Conclusion
By the end of Day 3, the OCR/Text route now has two complete baselines:
- Sparse retrieval: BM25
- Dense retrieval: text embedding retrieval

BM25 is currently the stronger baseline under the present setup.
## By Query Type
- parameter_lookup: BM25 better
- structure_legend_interpretation: BM25 clearly better
- component_localization: both weak, dense slightly less bad at top-10
- cross_page_consistency: BM25 slightly better
- similarity_based_interference: dense better at Recall@1, BM25 better overall
