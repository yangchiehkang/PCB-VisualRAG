# Week 4 Day 3 Subset Validation Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Day:** Day 3  
**Date:** 2026-05-07  
**Experiment Name:** Coarse-to-Fine Full MV Reranking Validation  
**Status:** Completed  

---

## 1. 今日目标

今日目标是在 Day 2 生成的 top-N candidate pages 上接入 Week 3 已经跑通的 Full Multi-vector Late Interaction reranker。

本日重点是验证：

- 每个 query 是否能正确读取候选页面；
- reranking 是否只发生在候选集合内；
- query embeddings 与 page embeddings 是否能正常加载；
- late interaction scoring 是否能正常生成最终排序；
- 不同 N 是否能独立输出 rerank run 文件。

---

## 2. 输入文件

| 类型 | 路径 |
|---|---|
| Candidate files | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_topN.tsv` |
| Query embeddings | `artifacts/embeddings/full_multivector/queries/*.npy` |
| Page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |

---

## 3. 输出文件

| N | Run 文件 | Validation 文件 |
|---:|---|---|
| 10 | `results\budgeted\coarse_to_fine\c2f_single_vector_N10_run.tsv` | `results\budgeted\coarse_to_fine\c2f_single_vector_N10_validation.csv` |
| 20 | `results\budgeted\coarse_to_fine\c2f_single_vector_N20_run.tsv` | `results\budgeted\coarse_to_fine\c2f_single_vector_N20_validation.csv` |
| 50 | `results\budgeted\coarse_to_fine\c2f_single_vector_N50_run.tsv` | `results\budgeted\coarse_to_fine\c2f_single_vector_N50_validation.csv` |
| 100 | `results\budgeted\coarse_to_fine\c2f_single_vector_N100_run.tsv` | `results\budgeted\coarse_to_fine\c2f_single_vector_N100_validation.csv` |

---

## 4. Rerank 运行统计

| N | Queries | Total Candidates | Total Scored | Avg Candidates / Query | Avg Rerank Latency / Query ms |
|---:|---:|---:|---:|---:|---:|
| 10 | 30 | 300 | 300 | 10.0000 | 10.814273 |
| 20 | 30 | 300 | 300 | 10.0000 | 8.275523 |
| 50 | 30 | 300 | 300 | 10.0000 | 7.613857 |
| 100 | 30 | 300 | 300 | 10.0000 | 7.747487 |

---

## 5. 验证结论

Day 3 已成功完成 coarse-to-fine second-stage reranking。

当前系统已经实现：

- 从 Day 2 candidate 文件读取 top-N 页面；
- 加载 Week 3 的 query token embeddings；
- 加载 Week 3 的 page multi-vector embeddings；
- 在候选集合内执行 sum-maxsim late interaction scoring；
- 为 N=10、20、50、100 分别输出 rerank run 文件；
- 生成 validation 文件检查 reranking 是否限定在候选集合内。

需要注意的是，Day 2 已发现当前 single-vector visual coarse run 的有效候选深度可能只有 top-10，因此不同 N 的 reranking 结果可能高度相似或完全相同。

该问题说明当前 C2F pipeline 已经跑通，但 single-vector coarse retriever 的候选召回能力和候选深度仍然是主要限制。
