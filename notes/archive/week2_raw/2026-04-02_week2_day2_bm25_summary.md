# Day 2 BM25 Baseline Summary

## Outputs
- data/metadata/ocr_corpus.jsonl
- results/bm25_run.tsv
- results/bm25_metrics.json

## Overall Metrics
- Recall@1: 0.1333
- Recall@3: 0.6833
- Recall@5: 0.6833
- Recall@10: 0.8833
- nDCG@10: 0.5241
- MRR: 0.4105

## By Query Type
- parameter_lookup: strong recall, weak top-1 ranking
- structure_legend_interpretation: best-performing category
- component_localization: failed completely under text-only BM25
- cross_page_consistency: partially effective, but weak for multi-page reasoning
- similarity_based_interference: good candidate recall, weak fine-grained disambiguation

## Initial Findings
BM25 can retrieve many correct pages within top-10 on OCR text, but ranking quality is limited.
The baseline works better for terminology-heavy queries than for visually grounded queries.
Component localization queries reveal a clear need for visual retrieval or multimodal reranking.
Similarity-based interference queries show that lexical matching is insufficient for fine-grained page discrimination.
