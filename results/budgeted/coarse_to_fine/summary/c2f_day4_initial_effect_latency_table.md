# Week 4 Day 4 Initial Effect-Latency Table

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4 Day 4  
**Experiment:** Coarse-to-Fine Evaluation  

---

## Table 4: Full MV 与 Coarse-to-Fine 检索结果对比

| Method | Recall@10 | MRR@10 | nDCG@10 | Latency | Actual Candidates / Query | Note |
|---|---:|---:|---:|---:|---:|---|
| Full Multi-vector | 0.1333 | 0.0644 | 0.0807 |  | full corpus | Full MV run found; latency should be filled from Week 3 cost log if available. |
| C2F N=10 | 0.2500 | 0.0628 | 0.1033 | 10.814267 ms/query | 10.0000 | coarse recall=0.2667; actual candidates/query=10.0000. |
| C2F N=20 | 0.2500 | 0.0628 | 0.1033 | 8.275533 ms/query | 10.0000 | coarse recall=0.2667; actual candidates/query is 10 due to limited coarse run depth. |
| C2F N=50 | 0.2500 | 0.0628 | 0.1033 | 7.613867 ms/query | 10.0000 | coarse recall=0.2667; actual candidates/query is 10 due to limited coarse run depth. |
| C2F N=100 | 0.2500 | 0.0628 | 0.1033 | 7.747500 ms/query | 10.0000 | coarse recall=0.2667; actual candidates/query is 10 due to limited coarse run depth. |

---

## Key Observation

当前 Day 4 的评测结果需要结合 Day 2 和 Day 3 一起解读。

- Day 2 显示 single-vector coarse recall 较低；
- Day 3 显示 N=10、20、50、100 的实际候选数均为每 query 10 个；
- 因此 Day 4 中不同 N 的效果与时延差异可能不明显；
- 当前实验主要验证 C2F pipeline 的完整闭环，而不是最终的候选预算曲线。
