# Week 6 Weekly Report：Quantized Budgeted Multi-vector Retrieval

**Project:** PCB_VisualRAG_Project  
**Week:** Week 6  
**Date:** 2026-05-07  
**Topic:** Joint Budgeting over Candidate Pages, Visual Tokens, and Vector Quantization  
**Status:** Completed  

---

## 1. Overview

This week focused on **Quantized Budgeted Multi-vector Retrieval** for PCB document-page retrieval. The goal was to evaluate how retrieval quality and system cost change when jointly controlling:

```text
N    = number of coarse candidate pages
M    = number of retained visual tokens per page
bits = vector quantization precision
```

Due to the current available candidate file, the experiments fixed:

```text
N = 10
```

and evaluated:

```text
M ∈ {8, 16, 24}
Compression ∈ {None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ}
```

This produced 15 main joint-budget configurations, plus an additional Day 5 bits sweep for PQ at M=24.

---

## 2. Experimental Design

### 2.1 Budget Triplet

The budgeted retrieval pipeline is defined by:

```text
Budget = (N, M, Compression / bits)
```

| Dimension | Meaning | Main Risk |
|---|---|---|
| N | Number of coarse candidate pages | Gold page missing from candidate pool |
| M | Number of retained visual tokens | Local evidence removed |
| bits | PQ quantization precision | Similarity ranking distortion |

---

### 2.2 Main Experiment Matrix

| Budget Level | N | M | Compression Settings |
|---|---:|---:|---|
| Low-budget | 10 | 8 | None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ |
| Mid-budget | 10 | 16 | None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ |
| High-budget | 10 | 24 | None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ |

---

## 3. Main Joint Budget Results

| N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---:|---:|---|---:|---:|---:|---:|---:|
| 10 | 8 | None | 0.266667 | 0.090688 | 0.124865 | 1.578125 | 4.872378 |
| 10 | 8 | PQ | 0.266667 | 0.050370 | 0.094891 | 0.006165 | 4.895973 |
| 10 | 8 | OPQ+PQ | 0.266667 | 0.042632 | 0.088811 | 0.006165 | 4.891157 |
| 10 | 8 | IVF+PQ | 0.266667 | 0.052910 | 0.096917 | 0.006165 | 4.808243 |
| 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.055317 | 0.099021 | 0.006165 | 4.803928 |
| 10 | 16 | None | 0.266667 | 0.090132 | 0.124232 | 3.156250 | 5.015381 |
| 10 | 16 | PQ | 0.266667 | 0.065000 | 0.107177 | 0.012329 | 4.952526 |
| 10 | 16 | OPQ+PQ | 0.266667 | 0.042315 | 0.088381 | 0.012329 | 4.980143 |
| 10 | 16 | IVF+PQ | 0.266667 | 0.065648 | 0.106069 | 0.012329 | 5.713590 |
| 10 | 16 | IVF+OPQ+PQ | 0.266667 | 0.077963 | 0.116206 | 0.012329 | 5.700525 |
| 10 | 24 | None | 0.266667 | 0.075450 | 0.114467 | 4.734375 | 5.317704 |
| 10 | 24 | PQ | 0.266667 | 0.088929 | 0.125460 | 0.018494 | 5.105066 |
| 10 | 24 | OPQ+PQ | 0.266667 | 0.082262 | 0.120075 | 0.018494 | 5.006297 |
| 10 | 24 | IVF+PQ | 0.266667 | 0.072540 | 0.112041 | 0.018494 | 5.099845 |
| 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.095688 | 0.129585 | 0.018494 | 5.406618 |

---

## 4. Representative Configurations

| Method | Run Name | Recall@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---|---:|---:|---:|---:|
| Best Quality Budgeted | w6_N10_M24_ivf_opq_pq | 0.266667 | 0.129585 | 0.018494 | 5.406618 |
| Best Trade-off Budgeted | w6_N10_M24_pq | 0.266667 | 0.125460 | 0.018494 | 5.105066 |
| Fastest Budgeted | w6_N10_M8_ivf_opq_pq | 0.266667 | 0.099021 | 0.006165 | 4.803928 |
| Best Uncompressed Baseline | w6_N10_M8_none | 0.266667 | 0.124865 | 1.578125 | 4.872378 |

---

## 5. Core Figures

### Figure 1: Quality vs. Index Size

```text
results/budgeted/joint_compression/figures/quality_vs_index_size.pdf
```

This figure shows that PQ-based compression substantially reduces estimated index size while preserving competitive nDCG@10.

---

### Figure 2: Quality vs. Retrieval Latency

```text
results/budgeted/joint_compression/figures/quality_vs_latency.pdf
```

This figure compares nDCG@10 against reranking latency under the reconstructed-embedding evaluation pipeline.

---

### Figure 3: Pareto Frontier

```text
results/budgeted/joint_compression/figures/pareto_frontier.pdf
```

This figure identifies non-dominated configurations under both index-size and latency cost dimensions.

---

## 6. Pareto Frontier Analysis

### 6.1 Index Size Frontier

| Run Name | M | Compression | nDCG@10 | Index Size MB |
|---|---:|---|---:|---:|
| w6_N10_M8_ivf_opq_pq | 8 | IVF+OPQ+PQ | 0.099021 | 0.006165 |
| w6_N10_M16_ivf_opq_pq | 16 | IVF+OPQ+PQ | 0.116206 | 0.012329 |
| w6_N10_M24_ivf_opq_pq | 24 | IVF+OPQ+PQ | 0.129585 | 0.018494 |

The index-size frontier is formed by the IVF+OPQ+PQ configurations at M8, M16, and M24.

---

### 6.2 Latency Frontier

| Run Name | M | Compression | nDCG@10 | Latency ms/query |
|---|---:|---|---:|---:|
| w6_N10_M8_ivf_opq_pq | 8 | IVF+OPQ+PQ | 0.099021 | 4.803928 |
| w6_N10_M8_none | 8 | None | 0.124865 | 4.872378 |
| w6_N10_M24_pq | 24 | PQ | 0.125460 | 5.105066 |
| w6_N10_M24_ivf_opq_pq | 24 | IVF+OPQ+PQ | 0.129585 | 5.406618 |

The latency frontier suggests that M24+PQ is a strong quality-latency trade-off point.

---

## 7. Budget Triplet Findings

### 7.1 N Determines the Recall Ceiling

Day 5 found that only 8 out of 30 queries have their gold page in the top-10 candidate pool:

```text
Coarse Recall Ceiling@10 = 8 / 30 = 0.266667
```

This exactly matches the Recall@10 of all joint-budget configurations. Therefore, N is the first-order budget dimension.

---

### 7.2 M Controls Fine-grained Evidence

M controls the number of retained visual tokens per page. Query q004 clearly benefits from larger M:

```text
nDCG@10_M8  = 0.289065
nDCG@10_M16 = 0.289065
nDCG@10_M24 = 0.500000
```

This indicates that some PCB queries require more visual tokens to preserve local evidence.

---

### 7.3 bits Controls Ranking Fidelity

The Day 5 bits sweep shows that PQ-b2 reduces index size but hurts ranking quality compared with PQ-b4:

| Setting | Recall@10 | MRR@10 | nDCG@10 | Index Size MB |
|---|---:|---:|---:|---:|
| PQ-b2 | 0.266667 | 0.063148 | 0.105743 | 0.009247 |
| PQ-b4 | 0.266667 | 0.088929 | 0.125460 | 0.018494 |

Thus, bits mainly controls ranking fidelity rather than the current Recall@10 ceiling.

---

## 8. Main Claim Draft

In PCB document-page retrieval, Budgeted Multi-vector Retrieval jointly controls the candidate-page budget N, the retained visual-token budget M, and the quantization precision bits. This budget triplet substantially reduces estimated index size while preserving competitive retrieval quality. The analysis shows that N determines the coarse-stage recall ceiling, M controls the amount of fine-grained visual evidence available to late interaction, and bits governs ranking fidelity under vector quantization. Together, these dimensions form a clear quality-cost Pareto frontier.

---

## 9. Weekly Conclusion

Week 6 completed the full experimental loop for quantized budgeted multi-vector retrieval. The experiments produced the main joint-budget results table, three core figures, Pareto frontier analysis, bits sensitivity analysis, and query-level failure diagnostics.

The strongest quality configuration is M24 + IVF+OPQ+PQ, the best trade-off configuration is M24 + PQ, and the fastest / lowest-cost budgeted configuration is M8 + IVF+OPQ+PQ. These results support the claim that budgeted multi-vector retrieval can significantly reduce index size while preserving competitive retrieval quality.
