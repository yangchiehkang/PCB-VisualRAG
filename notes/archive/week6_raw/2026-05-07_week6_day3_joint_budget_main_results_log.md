# Week 6 Day 3 实验日志：联合 Budget 主实验与结果表初版

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 3  
**Date:** 2026-05-07  
**Experiment:** Joint Budgeted Multi-vector Retrieval with Token Budget and Vector Compression  
**Budget Setting:** N=10, M ∈ {8, 16, 24}  
**Compression Settings:** None / PQ / OPQ+PQ / IVF+PQ / IVF+OPQ+PQ  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 3 的目标是在 Day 1 选定的代表性 budget 配置上运行联合实验，生成 Week 6 的主结果表初版。

原计划模板中使用：

```text
(N, M) ∈ {(20, 32), (50, 64), (100, 128)}
```

但根据当前真实实验环境，Day 1 已确认：

```text
当前 coarse candidates 仅支持 N=10
当前页面 full token 数为 49
M64 和 M128 超出当前有效 token 数
Week 5 已验证 M8 / M16 / M24 / M32 / M49
```

因此 Day 3 实际采用：

```text
(N, M) ∈ {(10, 8), (10, 16), (10, 24)}
```

每个 budget point 叠加以下压缩方式：

```text
None
PQ
OPQ+PQ
IVF+PQ
IVF+OPQ+PQ
```

总实验配置数为：

```text
3 token budgets × 5 compression settings = 15 configurations
```

今日核心目标是得到论文主实验所需的第一版原始数据表：

```text
N, M, Compression, Recall@10, MRR@10, nDCG@10, Index Size, Latency
```

---

## 2. 今日实验设置

### 2.1 Budget 配置

| Budget Level | N | M | Role |
|---|---:|---:|---|
| Low-budget | 10 | 8 | 极致轻量 token budget |
| Mid-budget | 10 | 16 | Week 5 最佳 trade-off token budget |
| High-budget | 10 | 24 | 高质量 / 保守压缩 token budget |

### 2.2 Compression 配置

| Compression | Description |
|---|---|
| None | 未压缩 baseline |
| PQ | Product Quantization |
| OPQ+PQ | Optimized Product Quantization followed by PQ |
| IVF+PQ | Inverted File Index with PQ |
| IVF+OPQ+PQ | IVF with OPQ rotation and PQ |

### 2.3 量化参数

Day 3 沿用 Day 2 已验证通过的稳定参数：

| Parameter | Value |
|---|---:|
| pq_m | 16 |
| bits | 4 |
| nlist | 8 |
| nprobe | 4 |

每个向量的估算 code size 为：

```text
16 subquantizers × 4 bits = 64 bits = 8 bytes/vector
```

---

## 3. 今日执行的脚本

### 3.1 批量构建压缩 embeddings

已运行：

```text
python scripts/compression/build_week6_joint_quantized_embeddings_day3.py
```

输出文件：

```text
results/budgeted/joint_compression/day3_main/day3_quantization_build_summary.csv
results/budgeted/joint_compression/day3_main/day3_quantization_build_summary.md
```

该脚本为以下 M 配置构建压缩 embeddings：

```text
M8:  PQ / OPQ+PQ / IVF+PQ / IVF+OPQ+PQ
M16: PQ / OPQ+PQ / IVF+PQ / IVF+OPQ+PQ
M24: PQ / OPQ+PQ / IVF+PQ / IVF+OPQ+PQ
```

对应输出目录包括：

```text
artifacts/embeddings/joint_compression/pages_M8_pq
artifacts/embeddings/joint_compression/pages_M8_opq_pq
artifacts/embeddings/joint_compression/pages_M8_ivf_pq
artifacts/embeddings/joint_compression/pages_M8_ivf_opq_pq

artifacts/embeddings/joint_compression/pages_M16_pq
artifacts/embeddings/joint_compression/pages_M16_opq_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_pq
artifacts/embeddings/joint_compression/pages_M16_ivf_opq_pq

artifacts/embeddings/joint_compression/pages_M24_pq
artifacts/embeddings/joint_compression/pages_M24_opq_pq
artifacts/embeddings/joint_compression/pages_M24_ivf_pq
artifacts/embeddings/joint_compression/pages_M24_ivf_opq_pq
```

---

### 3.2 批量运行 joint C2F reranking

已运行：

```text
python scripts/retrieval/run_week6_joint_c2f_day3.py
```

清洗后的 candidate 数据为：

| Item | Value |
|---|---:|
| Query Count | 30 |
| Candidate Rows | 300 |
| Avg Candidates / Query | 10.00 |

输出文件：

```text
results/budgeted/joint_compression/day3_main/day3_joint_rerank_latency.csv
results/budgeted/joint_compression/day3_main/day3_joint_rerank_latency.md
```

所有配置均成功完成 reranking：

```text
Valid queries: 30 / 30
Valid candidates: 300 / 300
```

---

### 3.3 批量评测 joint budget results

已运行：

```text
python scripts/evaluation/evaluate_week6_joint_budget_day3.py
```

输出主结果表：

```text
results/budgeted/joint_compression/summary/joint_budget_results.csv
results/budgeted/joint_compression/summary/joint_budget_results.md
results/budgeted/joint_compression/summary/joint_budget_results.xlsx
```

输出详细结果表：

```text
results/budgeted/joint_compression/day3_main/day3_joint_budget_results_detailed.csv
results/budgeted/joint_compression/day3_main/day3_joint_budget_results_detailed.md
```

---

### 3.4 代表点分析

已运行：

```text
python scripts/analysis/summarize_week6_day3_representative_points.py
```

输出文件：

```text
results/budgeted/joint_compression/day3_main/day3_representative_points.csv
results/budgeted/joint_compression/day3_main/day3_representative_points.md
results/budgeted/joint_compression/summary/day3_main_result_summary.md
```

---

## 4. Day 3 主结果表

### 4.1 Joint Budget Results

| N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query | Run Name |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| 10 | 8 | None | 0.266667 | 0.090688 | 0.124865 | 1.578125 | 4.872378 | w6_N10_M8_none |
| 10 | 8 | PQ | 0.266667 | 0.050370 | 0.094891 | 0.006165 | 4.895973 | w6_N10_M8_pq |
| 10 | 8 | OPQ+PQ | 0.266667 | 0.042632 | 0.088811 | 0.006165 | 4.891157 | w6_N10_M8_opq_pq |
| 10 | 8 | IVF+PQ | 0.266667 | 0.052910 | 0.096917 | 0.006165 | 4.808243 | w6_N10_M8_ivf_pq |
| 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.055317 | 0.099021 | 0.006165 | 4.803928 | w6_N10_M8_ivf_opq_pq |
| 10 | 16 | None | 0.266667 | 0.090132 | 0.124232 | 3.156250 | 5.015381 | w6_N10_M16_none |
| 10 | 16 | PQ | 0.266667 | 0.065000 | 0.107177 | 0.012329 | 4.952526 | w6_N10_M16_pq |
| 10 | 16 | OPQ+PQ | 0.266667 | 0.042315 | 0.088381 | 0.012329 | 4.980143 | w6_N10_M16_opq_pq |
| 10 | 16 | IVF+PQ | 0.266667 | 0.065648 | 0.106069 | 0.012329 | 5.713590 | w6_N10_M16_ivf_pq |
| 10 | 16 | IVF+OPQ+PQ | 0.266667 | 0.077963 | 0.116206 | 0.012329 | 5.700525 | w6_N10_M16_ivf_opq_pq |
| 10 | 24 | None | 0.266667 | 0.075450 | 0.114467 | 4.734375 | 5.317704 | w6_N10_M24_none |
| 10 | 24 | PQ | 0.266667 | 0.088929 | 0.125460 | 0.018494 | 5.105066 | w6_N10_M24_pq |
| 10 | 24 | OPQ+PQ | 0.266667 | 0.082262 | 0.120075 | 0.018494 | 5.006297 | w6_N10_M24_opq_pq |
| 10 | 24 | IVF+PQ | 0.266667 | 0.072540 | 0.112041 | 0.018494 | 5.099845 | w6_N10_M24_ivf_pq |
| 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.095688 | 0.129585 | 0.018494 | 5.406618 | w6_N10_M24_ivf_opq_pq |

---

## 5. 代表点识别

根据 `day3_main_result_summary.md`，Day 3 初步识别出以下代表配置：

| Category | Run Name | N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| Closest to best quality | w6_N10_M24_ivf_opq_pq | 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.095688 | 0.129585 | 0.018494 | 5.406618 |
| Lowest cost | w6_N10_M8_ivf_opq_pq | 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.055317 | 0.099021 | 0.006165 | 4.803928 |
| Best trade-off | w6_N10_M24_pq | 10 | 24 | PQ | 0.266667 | 0.088929 | 0.125460 | 0.018494 | 5.105066 |

---

## 6. 关键观察

### 6.1 Recall@10 在所有配置中保持一致

所有 15 组配置均得到：

```text
Recall@10 = 0.266667
```

这说明在当前 N=10 candidate pool 下，token budget 和 vector compression 的变化没有改变 top-10 是否命中的整体结果。

换言之，当前配置差异主要体现在：

```text
MRR@10
nDCG@10
Index Size
Latency
```

而不是 Recall@10。

---

### 6.2 压缩显著降低 estimated index size

未压缩配置的 index size 随 M 线性增长：

| M | None Index Size MB |
|---:|---:|
| 8 | 1.578125 |
| 16 | 3.156250 |
| 24 | 4.734375 |

压缩后 estimated index size 为：

| M | Compressed Index Size MB |
|---:|---:|
| 8 | 0.006165 |
| 16 | 0.012329 |
| 24 | 0.018494 |

对应压缩倍率均约为：

```text
256×
```

这验证了 Day 3 的主要成本侧结论：在当前 4-bit PQ 设置下，向量存储成本可以显著下降。

---

### 6.3 最高质量配置来自 M24 + IVF+OPQ+PQ

Day 3 最优 nDCG@10 配置为：

```text
w6_N10_M24_ivf_opq_pq
```

其指标为：

| Metric | Value |
|---|---:|
| Recall@10 | 0.266667 |
| MRR@10 | 0.095688 |
| nDCG@10 | 0.129585 |
| Index Size MB | 0.018494 |
| Latency ms/query | 5.406618 |

该配置不仅优于 M24 None，也优于 M8 None 和 M16 None 的 nDCG@10。

这说明在当前实验中，适度增加 token budget 到 M24，并叠加 IVF+OPQ+PQ，能够获得最好的排序质量。

---

### 6.4 最低成本配置来自 M8 压缩配置

最低 index size 对应 M8 下的压缩配置：

```text
Index Size MB = 0.006165
```

其中代表配置为：

```text
w6_N10_M8_ivf_opq_pq
```

指标为：

| Metric | Value |
|---|---:|
| Recall@10 | 0.266667 |
| MRR@10 | 0.055317 |
| nDCG@10 | 0.099021 |
| Index Size MB | 0.006165 |
| Latency ms/query | 4.803928 |

该配置是极致轻量点，适合作为最低成本边界。

---

### 6.5 最佳 trade-off 配置为 M24 + PQ

根据 Day 3 代表点分析，当前最佳 trade-off 配置为：

```text
w6_N10_M24_pq
```

指标为：

| Metric | Value |
|---|---:|
| Recall@10 | 0.266667 |
| MRR@10 | 0.088929 |
| nDCG@10 | 0.125460 |
| Index Size MB | 0.018494 |
| Latency ms/query | 5.105066 |

该配置的特点是：

- nDCG@10 高于所有 None 配置；
- MRR@10 接近 M8/M16 None；
- index size 远低于未压缩配置；
- latency 相对稳定；
- PQ 构建成本远低于 OPQ 相关方法。

---

## 7. 与 Day 2 的关系

Day 2 只验证了代表性配置：

```text
N=10, M=16
```

Day 3 将该流程扩展到：

```text
M ∈ {8, 16, 24}
```

并完成了 15 组联合 budget 实验。Day 2 证明 pipeline 可运行，Day 3 生成了主结果表初版。

其中 M16 的 Day 3 结果与 Day 2 结果整体一致：

- Recall@10 均保持 0.266667；
- PQ / IVF+PQ / IVF+OPQ+PQ 的排序趋势基本一致；
- OPQ 相关方法仍表现出较高构建成本；
- 压缩 index size 仍为 0.012329 MB。

---

## 8. 今日遇到的问题与注意事项

### 8.1 当前 N 维度仍固定为 10

由于当前 candidate 文件为：

```text
artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
```

Day 3 实验仍固定：

```text
N = 10
```

因此 Day 3 的联合 budget 实际形式为：

```text
Budget = (N fixed, M, Compression)
```

后续若生成 top20 / top50 / top100 candidates，可扩展为完整三维 budget：

```text
Budget = (N, M, Compression)
```

---

### 8.2 当前 latency 不代表真实 IVF ANN 加速

当前 pipeline 为了兼容既有 late interaction reranking，使用 reconstructed `.npy` embeddings 进行评分。因此：

- latency 主要反映 reranking pipeline 的运行时间；
- IVF 的真实 ANN 加速优势没有完全体现；
- Index Size 使用 `estimated_code_size_mb` 作为压缩体积；
- reconstructed file size 仅用于兼容实验流程，不作为压缩后真实存储成本。

---

### 8.3 OPQ 训练成本较高

从 Day 2 和 Day 3 结果看，OPQ 相关方法通常具有较高 build time。尤其在小规模训练样本下，FAISS 会出现训练样本不足 warning。

因此后续报告中需要谨慎表述：

- OPQ 可能降低重建误差；
- OPQ 并不总是带来更高排序质量；
- OPQ 会带来明显额外训练成本；
- 在当前小数据设置下，PQ 的简单性和稳定性更有优势。

---

## 9. 今日完成文件清单

### 9.1 Day 3 Build Summary

```text
results/budgeted/joint_compression/day3_main/day3_quantization_build_summary.csv
results/budgeted/joint_compression/day3_main/day3_quantization_build_summary.md
```

### 9.2 Day 3 Reranking Latency

```text
results/budgeted/joint_compression/day3_main/day3_joint_rerank_latency.csv
results/budgeted/joint_compression/day3_main/day3_joint_rerank_latency.md
```

### 9.3 Day 3 Detailed Results

```text
results/budgeted/joint_compression/day3_main/day3_joint_budget_results_detailed.csv
results/budgeted/joint_compression/day3_main/day3_joint_budget_results_detailed.md
```

### 9.4 Joint Budget Main Results

```text
results/budgeted/joint_compression/summary/joint_budget_results.csv
results/budgeted/joint_compression/summary/joint_budget_results.md
results/budgeted/joint_compression/summary/joint_budget_results.xlsx
```

### 9.5 Representative Points

```text
results/budgeted/joint_compression/day3_main/day3_representative_points.csv
results/budgeted/joint_compression/day3_main/day3_representative_points.md
results/budgeted/joint_compression/summary/day3_main_result_summary.md
```

---

## 10. Day 3 验收状态

| Requirement | Status |
|---|---|
| 所有代表 budget 点完成压缩实验 | Completed |
| 15 组配置全部生成 run 文件 | Completed |
| 15 组配置全部生成 latency 统计 | Completed |
| 15 组配置全部完成 metrics 评测 | Completed |
| joint_budget_results.csv 已生成 | Completed |
| joint_budget_results.md 已生成 | Completed |
| joint_budget_results.xlsx 已生成 | Completed |
| 主结果表初版已完成 | Completed |
| 代表点已识别 | Completed |

---

## 11. 今日结论

Week 6 Day 3 已成功完成联合 budget 主实验初版。在固定 N=10 的条件下，本日系统性评估了 M8、M16、M24 三个 token budget，并对每个 budget 叠加 None、PQ、OPQ+PQ、IVF+PQ 和 IVF+OPQ+PQ 五种压缩设置，共 15 组配置。

实验结果显示，所有配置均保持 Recall@10 = 0.266667，说明当前 candidate pool 下压缩与 token budget 变化没有影响 top-10 命中率。成本方面，4-bit PQ 系列方法将 estimated index size 从 MB 级降低到 0.0062–0.0185 MB 区间，约实现 256× 的估算压缩倍率。

质量方面，最高 nDCG@10 配置为 M24 + IVF+OPQ+PQ，达到 nDCG@10 = 0.129585；最低成本配置为 M8 + IVF+OPQ+PQ，index size 仅为 0.006165 MB；当前最佳 trade-off 配置为 M24 + PQ，在较低 index size 下取得 nDCG@10 = 0.125460。

Day 3 已获得 Week 6 论文主结果所需的关键原始数据，可以进入 Day 4 的可视化分析与 Pareto frontier 讨论。
