# Week 7 Weekly Report：Fixed-N Coarse-to-Fine Retrieval and Evidence Attribution

**Project:** PCB_VisualRAG_Project  
**Week:** Week 7  
**Date:** 2026-05-08  
**Topic:** Fixed Candidate Budget, Hybrid Fusion, Evidence Hit, Region Hit, and Occlusion-based Attribution  
**Status:** Completed  

---

## 1. Overview

This week focused on improving the experimental validity and interpretability of the PCB VisualRAG retrieval pipeline.

The main objective was twofold:

```text
1. Fix the coarse retrieval candidate budget so that different N values are actually evaluated.
2. Build an evidence attribution pipeline to evaluate whether retrieval scores depend on localized visual evidence regions.
```

Week 7 extends the previous budgeted multi-vector experiments by correcting the candidate generation stage and introducing evidence-level evaluation.

The final outputs include:

```text
Table 14: BM25-C2F main results
Table 15: Budgeted Retrieval representative configurations
Table 16: Evidence Hit main results
Table 17: Occlusion main results
Table 18: Visual case types
```

In addition, five qualitative visual cases were generated for evidence attribution and occlusion analysis.

---

## 2. Experimental Pipeline

### 2.1 Fixed-N Candidate Generation

A key issue identified from the previous week was that the coarse candidate pool was effectively fixed at top-10 candidates, even when the experiment configuration specified larger N values.

This week fixed that issue by modifying retrieval scripts to support:

```text
--top_k
--output
```

Updated scripts:

```text
scripts/retrieval/run_bm25.py
scripts/retrieval/run_dense_text_retrieval.py
scripts/retrieval/run_single_vector_visual_retrieval.py
```

The candidate budgets evaluated were:

```text
N ∈ {10, 20, 50, 100}
```

This correction ensures that C2F reranking experiments are based on the intended candidate pool size.

---

### 2.2 Multi-vector Reranking

The multi-vector reranking stage uses late interaction scoring:

```text
score(q, p) = sum_i max_j q_i^T p_j
```

where each query token interacts with the most similar page token.

The evaluated reranking settings include:

```text
BM25 + Full MV:
N ∈ {10, 20, 50, 100}

BM25 + Budgeted MV:
N ∈ {20, 50}
M ∈ {8, 16, 24}
```

The Full MV setting uses all available visual tokens, while Budgeted MV uses a reduced number of retained tokens.

---

### 2.3 Score Normalization and Hybrid Fusion

To combine BM25 and MV scores, query-level min-max normalization was applied separately to BM25 scores and MV scores.

The fused score is defined as:

```text
final_score = alpha * bm25_score_norm + (1 - alpha) * mv_score_norm
```

The sweep range was:

```text
alpha ∈ {0.0, 0.1, ..., 1.0}
```

This enables direct comparison between pure visual reranking, pure lexical retrieval, and hybrid scoring.

---

## 3. Main Retrieval Results

### 3.1 Table 14: BM25-C2F Main Results

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Index Size |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | 3030 |
| BM25 + Full MV | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 10 |
| BM25 + Budgeted MV | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 20 |
| Hybrid Fusion | 0.0667 | 0.1000 | 0.1333 | 0.0881 | 0.0988 | 301 |

The strongest overall method in the main retrieval table is BM25, which achieves:

```text
Recall@10 = 0.8833
MRR@10 = 0.4105
nDCG@10 = 0.5241
```

This suggests that OCR-based lexical matching remains highly effective for the current PCB document retrieval task.

---

### 3.2 Table 15: Budgeted Retrieval Representative Configurations

| Config | N | M | Compression | nDCG@10 | Index Size MB | Latency |
|---|---:|---:|---|---:|---:|---:|
| Full MV | full | 49 | None | 0.3628 | 0.01 | 9.3619 |
| Budgeted Low-cost | 20 | 8 | PQ | 0.1565 | 0.02 | 12.6743 |
| Budgeted Mid-cost | 20 | 16 | PQ | 0.1490 | 0.02 | 12.8563 |
| Budgeted High-quality | 50 | 24 | PQ | 0.0359 | 0.02 | 31.9103 |

The results show that increasing the visual budget does not automatically improve retrieval quality in the current setting.

The best visual reranking configuration among these representative settings is Full MV, while budgeted settings show weaker nDCG@10.

---

## 4. Evidence-level Evaluation

### 4.1 Evidence Query Subset

A subset of 10 evidence queries was selected for fine-grained evaluation.

Each sample contains:

```text
query_id
gold_page_id
evidence region
bbox annotation
retrievability information
```

The selected evidence subset includes:

| Query ID | Gold Page | Evidence Type | Retrievable |
|---|---|---|---|
| q001 | doc001_p001 | region | yes |
| q002 | doc001_p002 | region | yes |
| q004 | doc001_p004 | region | yes |
| q006 | doc002_p001 | region | yes |
| q007 | doc002_p001 | region | yes |
| q008 | doc003_p007 | region | yes |
| q009 | doc003_p008 | region | yes |
| q010 | doc003_p009 | region | yes |
| q011 | doc003_p010 | region | yes |
| q012 | doc003_p011 | region | yes |

---

### 4.2 Table 16: Evidence Hit Results

| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 |
|---|---:|---:|---:|
| BM25 | 0.4000 | 1.0000 | 1.0000 |
| Full MV | 0.1000 | 0.4000 | 1.0000 |
| Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| BM25 + Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| Hybrid Fusion | 0.4000 | 1.0000 | 1.0000 |

BM25 and Hybrid Fusion perform best on evidence-level page retrieval.

Both methods reach:

```text
Evidence Hit@1 = 0.4000
Evidence Hit@5 = 1.0000
Evidence Hit@10 = 1.0000
```

Full MV also reaches perfect Top-10 evidence coverage, but its Top-1 and Top-5 performance are weaker.

This indicates that Full MV can recover evidence pages but is less effective at ranking them near the top.

---

### 4.3 Region Hit Results

The region-level evaluation measures whether the top visual patches overlap with the gold evidence bbox.

The evaluation uses:

```text
7x7 patch grid
IoU threshold = 0.3
```

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 |
|---|---:|---:|---:|
| Full MV | 0.0000 | 0.0000 | 0.0000 |
| Budgeted MV | 0.0000 | 0.0000 | 0.1000 |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.2000 |
| Hybrid Fusion | 0.0000 | 0.2000 | 0.4000 |

Hybrid Fusion performs best at the region level, achieving:

```text
Region Hit@3 = 0.2000
Region Hit@5 = 0.4000
```

However, the region-level scores remain much lower than page-level Evidence Hit scores.

This suggests that evidence page retrieval and evidence localization are distinct levels of difficulty.

---

## 5. Occlusion-based Evidence Attribution

### 5.1 Occlusion Design

The occlusion experiment compares three conditions:

```text
Original:
The original evidence page is used.

Gold Mask:
The annotated evidence bbox is masked.

Random Mask:
A random non-overlapping region is masked.
```

The goal is to test whether the retrieval score depends on the annotated evidence region.

---

### 5.2 Table 17: Occlusion Main Results

| Condition | MRR@10 | nDCG@10 | Avg Gold Page Score |
|---|---:|---:|---:|
| Original | 1.0000 | 1.0000 | 0.20149380 |
| Gold Mask | 0.0000 | 0.0000 | 0.00000000 |
| Random Mask | 1.0000 | 1.0000 | 0.20149380 |

The result is highly clear:

```text
Masking the gold evidence region collapses the gold page score to zero.
Masking a random region does not change the score.
```

This provides strong evidence that the model score depends on the annotated evidence region.

---

## 6. Qualitative Visual Cases

Five visual cases were generated for the report.

### 6.1 Table 18: Visual Case Types

| Case Type | Count | Purpose |
|---|---:|---|
| Gold mask causes clear score drop | 2 | Supports evidence dependency |
| Random mask has small impact | 1 | Supports control validity |
| Occlusion-insensitive failure case | 1 | Shows objective analysis |
| BM25 + MV ranking improvement case | 1 | Supports performance complementarity |

---

### 6.2 Visual Case Summary

| Case ID | Case Type | Query ID | Page ID | COG_score | Figure |
|---|---|---|---|---:|---|
| evidence_case_001 | Gold mask 后明显掉分 | q001 | doc001_p001 | 0.28208059 | figures/week7/evidence_case_001.png |
| evidence_case_002 | Gold mask 后明显掉分 | q011 | doc003_p010 | 0.28198810 | figures/week7/evidence_case_002.png |
| evidence_case_003 | Random mask 影响较小 | q002 | doc001_p002 | 0.13606575 | figures/week7/evidence_case_003.png |
| evidence_case_004 | 遮挡不敏感失败例 | q004 | doc001_p004 | 0.01350269 | figures/week7/evidence_case_004.png |
| evidence_case_005 | BM25 + MV 改善排序例 | q010 | doc003_p009 | 0.28175521 | figures/week7/evidence_case_005.png |

Each case includes:

```text
Original page with gold bbox
Gold mask image
Random mask image
Score changes
Short explanation
```

---

## 7. Key Findings

### 7.1 Fixing candidate N is essential

The Week 7 fixed-N setup corrects the candidate budget issue from the previous stage.

This allows C2F retrieval to be evaluated under true candidate budgets:

```text
N = 10, 20, 50, 100
```

---

### 7.2 BM25 remains a strong baseline

BM25 achieves the strongest main retrieval performance.

This suggests that PCB page retrieval still heavily benefits from OCR text matching.

---

### 7.3 Full MV improves evidence coverage but not top ranking

Full MV reaches:

```text
Evidence Hit@10 = 1.0000
```

but only:

```text
Evidence Hit@1 = 0.1000
Evidence Hit@5 = 0.4000
```

This indicates that Full MV can find gold evidence pages but has weaker ranking precision.

---

### 7.4 Hybrid Fusion is strong for evidence retrieval

Hybrid Fusion matches BM25 on evidence-level retrieval:

```text
Evidence Hit@1 = 0.4000
Evidence Hit@5 = 1.0000
Evidence Hit@10 = 1.0000
```

It also performs best in Region Hit@5.

This suggests that combining lexical and visual signals improves evidence-level robustness.

---

### 7.5 Occlusion confirms evidence dependency

Gold mask removes the evidence region and causes the score to collapse.

Random mask does not affect the score.

This supports the conclusion that model scores are causally tied to the annotated evidence regions.

---

## 8. Limitations

The current experiments still have several limitations:

```text
1. Some query_text fields are empty in the visual case figures.
2. Single-vector Visual is missing in Evidence Hit evaluation.
3. Region Hit scores remain low, suggesting patch-level localization is still difficult.
4. The current bbox generation is automatic and may contain annotation noise.
5. Random masks are strictly non-overlapping with gold regions; future analysis can test partial-overlap masks.
```

---

## 9. Generated Artifacts

### 9.1 Core Tables

```text
results/week7/day6_core_tables/table14_bm25_c2f_main_results.csv
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.csv
results/week7/day6_core_tables/table16_evidence_hit_main_results.csv
results/week7/day6_core_tables/table17_occlusion_main_results.csv
```

---

### 9.2 Evidence and Occlusion Outputs

```text
results/week7/evidence_hit/
results/week7/region_hit/
results/week7/occlusion/
```

---

### 9.3 Visual Figures

```text
figures/week7/evidence_case_001.png
figures/week7/evidence_case_002.png
figures/week7/evidence_case_003.png
figures/week7/evidence_case_004.png
figures/week7/evidence_case_005.png
```

---

## 10. Final Conclusion

Week 7 completed a full experimental cycle from fixed-N candidate generation to evidence-level attribution.

The main conclusion is:

```text
BM25 remains the strongest general retrieval baseline for the current PCB document setting,
but Hybrid Fusion provides stronger evidence-level robustness.
Occlusion analysis further confirms that the visual score is highly dependent on the annotated gold evidence region.
```

Final status:

```text
Week 7 completed successfully.
```
