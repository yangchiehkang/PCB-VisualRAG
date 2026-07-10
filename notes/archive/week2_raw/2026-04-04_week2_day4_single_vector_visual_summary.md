# Day 4 Single-vector Visual Retrieval Summary

## Outputs
- results/single_vector_visual_run.tsv
- results/single_vector_visual_metrics.json

## Model / Setup
- Visual encoder: openai/clip-vit-base-patch32
- Page representation: one global image embedding per page
- Query representation: CLIP text embedding
- Retrieval backend: FAISS IndexFlatIP
- Similarity: cosine-equivalent via L2-normalized inner product

## Overall Metrics
| Metric | BM25 | Dense Text | Single-vector Visual |
|---|---:|---:|---:|
| Recall@1 | 0.1333 | 0.1000 | 0.0000 |
| Recall@3 | 0.6833 | 0.4500 | 0.0833 |
| Recall@5 | 0.6833 | 0.6000 | 0.0833 |
| Recall@10 | 0.8833 | 0.8000 | 0.2500 |
| nDCG@10 | 0.5241 | 0.4420 | 0.1041 |
| MRR | 0.4105 | 0.3358 | 0.0664 |

## By Query Type
| Query Type | Recall@10 | MRR |
|---|---:|---:|
| parameter_lookup | 0.5000 | 0.0833 |
| structure_legend_interpretation | 0.4000 | 0.0533 |
| component_localization | 0.5000 | 0.0500 |
| cross_page_consistency | 0.1250 | 0.1250 |
| similarity_based_interference | 0.1765 | 0.0564 |

## Key Findings
- Single-vector visual retrieval performed substantially worse than both BM25 and dense text retrieval.
- The model failed to retrieve relevant pages at rank 1 for all query types.
- Some relevant pages were retrieved within top-10, especially for component_localization and parameter_lookup.
- However, global page-level visual embeddings were too coarse to support stable page retrieval for this task.
- The results suggest that page retrieval in PCB manuals is not well solved by a pure global-image baseline.

## Interpretation
This baseline is still useful because it establishes a lower-bound visual retrieval reference.
The result indicates that:
1. OCR/text signals remain much stronger for first-stage retrieval;
2. global visual embeddings lose fine-grained component and layout details;
3. future improvements likely require multimodal fusion, region-level retrieval, or reranking.

## Conclusion
By the end of Day 4, the project now has three completed first-stage baselines:
- BM25 sparse text retrieval
- Dense text embedding retrieval
- Single-vector visual retrieval

Among them, BM25 is currently the strongest baseline.
Day 4 established the first visual retrieval baseline using single-vector CLIP embeddings. The baseline successfully ran end-to-end, but its retrieval quality was substantially worse than both BM25 and dense text retrieval. This suggests that global page-level visual embeddings are too coarse for PCB manual page retrieval, and that future gains are more likely to come from multimodal fusion, local-region modeling, or reranking rather than pure visual first-stage retrieval.