# Week 8 Lightweight Visual RAG Experiment Summary

## Status

```text
QA input mapping: complete
Ollama VLM inference: complete
Rule-based QA evaluation: complete
Result tables: complete
```

## Key Output Files

```text
results/week8/visual_rag/qa_inputs.csv
results/week8/visual_rag/qa_outputs_ollama.csv
results/week8/visual_rag/qa_outputs_manual_filled.csv
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
results/week8/visual_rag/tables/table21_retrieval_vs_qa_results.csv
results/week8/visual_rag/tables/table22_qa_error_breakdown.csv
results/week8/visual_rag/tables/table23_retrieval_quality_vs_qa_quality.csv
```

## Input Mapping

setting,total,mapped_page_id,mapped_image_path,gold_page_hits,used_run_file
Gold Evidence,10,10,10,10,
BM25,10,10,10,4,results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv
Full MV,10,10,10,1,results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv
Hybrid Fusion,10,10,10,4,results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv
Budgeted MV,10,10,10,1,results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv
Gold Masked,10,10,10,10,
Random Masked,10,10,10,10,


## Main Results

# Table 19: Lightweight Visual RAG Main Results

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count | masked_evidence_count |
|---|---|---|---|---|---|---|---|---|---|---|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 | 0 |
| Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 0.5000 | 0 | 5 | 4 | 0 |
| Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 0 | 5 | 1 | 0 |
| Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 0.7000 | 0 | 3 | 6 | 0 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 |

## Occlusion Results

# Table 20: Occlusion Downstream Results

| setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | no_answer_count | wrong_page_count | hallucination_count | masked_evidence_count | accuracy_delta_vs_gold | support_delta_vs_gold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gold Evidence | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| Gold Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| Random Masked | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 |

## Retrieval vs QA

# Table 21: Retrieval vs QA Results

| retrieval_condition | setting | num_cases | gold_page_rate | answer_accuracy | evidence_supported_rate | unknown_rate | concrete_answer_rate | wrong_page_count | hallucination_count |
|---|---|---|---|---|---|---|---|---|---|
| BM25 | BM25 | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 5 | 1 |
| Full MV | Full MV | 10 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 0.5000 | 5 | 4 |
| Hybrid Fusion | Hybrid Fusion | 10 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 0.5000 | 5 | 1 |
| Budgeted MV | Budgeted MV | 10 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 0.7000 | 3 | 6 |

## Retrieval Quality vs QA Quality

# Table 23: Retrieval Quality vs QA Quality

| setting | num_cases | gold_page_hits | retrieval_gold_hit_rate | answer_accuracy | evidence_supported_rate | unknown_rate | hallucination_count | used_run_file |
|---|---|---|---|---|---|---|---|---|
| Gold Evidence | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |
| BM25 | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 | results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha1p0_run.tsv |
| Full MV | 10 | 1 | 0.1000 | 0.1000 | 0.6000 | 0.5000 | 4 | results\week7\c2f_fixed_N\bm25_fullmv_N10_run.tsv |
| Hybrid Fusion | 10 | 4 | 0.4000 | 0.4000 | 0.9000 | 0.5000 | 1 | results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha1p0_run.tsv |
| Budgeted MV | 10 | 1 | 0.1000 | 0.1000 | 0.4000 | 0.3000 | 6 | results\week7\c2f_fixed_N\bm25_budgetmv_N20_M8_none_run.tsv |
| Gold Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |
| Random Masked | 10 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 |  |

## Experiment-Level Conclusion

```text
The first-pass lightweight Visual RAG downstream experiment is complete.
The results show that answer correctness is strongly tied to whether the retrieved page matches the gold evidence page.
In the current page-level QA setup, Gold Masked and Random Masked conditions do not reduce QA accuracy.
The occlusion result should therefore be reported cautiously as a negative or inconclusive downstream occlusion finding under the current setup.
```
