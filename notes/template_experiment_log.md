# Experiment Log Template

**Project:** PCB_VisualRAG_Project  
**Date:** YYYY-MM-DD  
**Experiment Name:**  
**Stage:**  
**Author:** 杨杰康  
**Status:** Planned / Running / Completed / Failed  

---

## 1. Experiment Objective

Briefly describe the goal of this experiment.

Example:

- Validate BM25 top-N + Full MV reranking.
- Test token budget settings for multi-vector retrieval.
- Compare performance-cost trade-off under different candidate sizes.

---

## 2. Background and Motivation

Explain why this experiment is needed.

Recommended points:

- What previous result motivates this experiment?
- What hypothesis is being tested?
- How does this experiment support the thesis narrative?

---

## 3. Inputs

| Input | Path / Value |
|---|---|
| Corpus |  |
| Queries |  |
| Qrels |  |
| Page embeddings |  |
| Query embeddings |  |
| Baseline run |  |
| Config file |  |

---

## 4. Experimental Setup

### 4.1 Model / Method

| Item | Setting |
|---|---|
| Retriever |  |
| Reranker |  |
| Embedding model |  |
| Similarity |  |
| Aggregation |  |
| Candidate size |  |
| Token budget |  |
| Top-k output |  |

---

### 4.2 Key Parameters

| Parameter | Value |
|---|---|
| `N` candidate budget |  |
| `M` token budget |  |
| Vector dim |  |
| Normalization |  |
| Random seed |  |
| Device |  |

---

## 5. Commands

Record the exact command used to run the experiment.

Example:

- `python scripts/retrieval/run_xxx.py --config configs/xxx.yaml`

---

## 6. Outputs

| Output | Path |
|---|---|
| Run file |  |
| Metrics file |  |
| Summary CSV |  |
| Query-level analysis |  |
| Log file |  |

---

## 7. Overall Metrics

| Metric | Value |
|---|---:|
| Recall@1 |  |
| Recall@5 |  |
| Recall@10 |  |
| MRR |  |
| nDCG@10 |  |

---

## 8. Cost Metrics

| Cost Item | Value |
|---|---:|
| Vectors per page |  |
| Index size |  |
| Avg query latency |  |
| Total runtime |  |
| Memory usage |  |

---

## 9. Query-type Analysis

| Query Type | Recall@10 | MRR | Notes |
|---|---:|---:|---|
| `parameter_lookup` |  |  |  |
| `structure_legend_interpretation` |  |  |  |
| `component_localization` |  |  |  |
| `cross_page_consistency` |  |  |  |
| `similarity_based_interference` |  |  |  |

---

## 10. Key Observations

Record important findings.

Examples:

- Which method performs best?
- Which query types improve?
- Which query types fail?
- Are there unexpected results?
- Is the cost acceptable?

---

## 11. Error Analysis

### 11.1 Successful Cases

| Query ID | Observation |
|---|---|
|  |  |

---

### 11.2 Failed Cases

| Query ID | Observation |
|---|---|
|  |  |

---

## 12. Issues and Fixes

| Issue | Cause | Fix |
|---|---|---|
|  |  |  |

---

## 13. Conclusion

Summarize the experiment in 3–5 bullet points.

- 
- 
- 

---

## 14. Next Steps

List concrete next actions.

- 
- 
- 
