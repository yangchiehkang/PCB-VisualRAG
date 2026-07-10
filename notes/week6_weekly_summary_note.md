# Week 6 Day 6 Note：主实验材料汇总与论文级结论整理

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 6  
**Date:** 2026-05-07  
**Theme:** Quantized Budgeted Multi-vector Retrieval  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 6 的目标是汇总 Week 6 全部实验材料，形成可进入论文主实验章节的结果包，并整理本周核心发现。

Week 6 围绕预算三元组展开：

```text
Budget = (N, M, bits / compression)
```

其中：

```text
N    = coarse retrieval candidate page budget
M    = retained page token budget
bits = vector quantization precision
```

本周实验重点不是单纯做工程压缩，而是回答：

```text
在 PCB 文档页面检索任务中，预算应优先分配给 coarse candidate、局部 visual tokens，还是向量量化精度？
```

---

## 2. 本周实验闭环

Week 6 已完成从实验设计到论文图表的完整闭环。

| Day | Theme | Status |
|---:|---|---|
| Day 1 | 设计联合 budget 实验矩阵 | Completed |
| Day 2 | 验证 PQ / OPQ / IVF-PQ 压缩 pipeline | Completed |
| Day 3 | 跑完 15 组联合 budget 主实验 | Completed |
| Day 4 | 绘制三张核心图并识别 Pareto frontier | Completed |
| Day 5 | 提炼预算三元组结论与失败案例 | Completed |
| Day 6 | 汇总主实验材料并写周报 | Completed |

---

## 3. Week 6 主实验设置

### 3.1 实验约束

当前真实实验环境存在两个关键约束：

```text
1. 当前 coarse candidate 文件仅支持 N=10
2. 当前每页 full multi-vector token 数为 49
```

因此 Week 6 主实验固定：

```text
N = 10
```

并选择三个代表 token budget：

```text
M ∈ {8, 16, 24}
```

每个 M 叠加五种 compression setting：

```text
None
PQ
OPQ+PQ
IVF+PQ
IVF+OPQ+PQ
```

总配置数：

```text
3 M budgets × 5 compression settings = 15 configurations
```

---

## 4. 联合 Budget 主结果表

Week 6 主结果文件为：

```text
results/budgeted/joint_compression/summary/joint_budget_results.csv
results/budgeted/joint_compression/summary/joint_budget_results.md
results/budgeted/joint_compression/summary/joint_budget_results.xlsx
```

### 4.1 Main Joint Budget Results

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

## 5. 代表性最优点对比表

| Method | Run Name | Recall@10 | nDCG@10 | Index Size MB | Latency ms/query | Note |
|---|---|---:|---:|---:|---:|---|
| Full Multi-vector Reference | Week 5 M49 reference | N/A | N/A | N/A | N/A | Week 6 未重新压缩 M49；作为外部 reference |
| Best Quality Budgeted | w6_N10_M24_ivf_opq_pq | 0.266667 | 0.129585 | 0.018494 | 5.406618 | 当前最高 nDCG@10 |
| Best Trade-off Budgeted | w6_N10_M24_pq | 0.266667 | 0.125460 | 0.018494 | 5.105066 | 质量接近最优，latency 更低，方法简单 |
| Fastest Budgeted | w6_N10_M8_ivf_opq_pq | 0.266667 | 0.099021 | 0.006165 | 4.803928 | 最低成本且 latency 最低 |
| Best Uncompressed Baseline | w6_N10_M8_none | 0.266667 | 0.124865 | 1.578125 | 4.872378 | 未压缩中表现较强 |

---

## 6. 三张核心图

Week 6 Day 4 已生成三张核心图。

### 6.1 Quality vs. Index Size

```text
results/budgeted/joint_compression/figures/quality_vs_index_size.pdf
results/budgeted/joint_compression/figures/quality_vs_index_size.png
```

该图显示 compressed configurations 集中在极低 index size 区域，同时部分配置保持甚至超过 uncompressed baseline 的 nDCG@10。

---

### 6.2 Quality vs. Retrieval Latency

```text
results/budgeted/joint_compression/figures/quality_vs_latency.pdf
results/budgeted/joint_compression/figures/quality_vs_latency.png
```

该图显示当前 reconstructed-embedding reranking pipeline 下，不同压缩配置的 latency 差异较小。IVF 的真实 ANN 加速优势尚未在当前流程中完全体现。

---

### 6.3 Pareto Frontier

```text
results/budgeted/joint_compression/figures/pareto_frontier.pdf
results/budgeted/joint_compression/figures/pareto_frontier.png
```

该图展示了：

```text
1. Quality vs. Index Size Pareto frontier
2. Quality vs. Latency Pareto frontier
```

---

## 7. Pareto Frontier 总结

### 7.1 Index Size Pareto Frontier

Index-size frontier 包含：

| Run Name | M | Compression | nDCG@10 | Index Size MB |
|---|---:|---|---:|---:|
| w6_N10_M8_ivf_opq_pq | 8 | IVF+OPQ+PQ | 0.099021 | 0.006165 |
| w6_N10_M16_ivf_opq_pq | 16 | IVF+OPQ+PQ | 0.116206 | 0.012329 |
| w6_N10_M24_ivf_opq_pq | 24 | IVF+OPQ+PQ | 0.129585 | 0.018494 |

结论：

```text
M8 → M16 → M24 构成清晰的质量–索引大小 Pareto frontier。
```

---

### 7.2 Latency Pareto Frontier

Latency frontier 包含：

| Run Name | M | Compression | nDCG@10 | Latency ms/query |
|---|---:|---|---:|---:|
| w6_N10_M8_ivf_opq_pq | 8 | IVF+OPQ+PQ | 0.099021 | 4.803928 |
| w6_N10_M8_none | 8 | None | 0.124865 | 4.872378 |
| w6_N10_M24_pq | 24 | PQ | 0.125460 | 5.105066 |
| w6_N10_M24_ivf_opq_pq | 24 | IVF+OPQ+PQ | 0.129585 | 5.406618 |

结论：

```text
M24 + PQ 是当前更稳健的 quality-latency trade-off 点。
```

---

## 8. 预算三元组结论

### 8.1 N 控制 Recall Ceiling

Day 5 发现：

```text
Gold page in top-10 candidate pool = 8 / 30
Coarse Recall Ceiling@10 = 0.266667
```

这与所有 Day 3 joint budget 配置的 Recall@10 完全一致：

```text
Recall@10 = 0.266667
```

因此：

```text
N 是第一优先级预算。
```

如果 gold page 没有进入 coarse candidate pool，后续 M、bits、compression 无法恢复该结果。

---

### 8.2 M 控制局部证据保留

M 控制每个 page 保留的 visual token 数量。

代表 query：

```text
q004
```

在 None 配置下：

```text
nDCG@10_M8  = 0.289065
nDCG@10_M16 = 0.289065
nDCG@10_M24 = 0.500000
Delta M24 - M8 = +0.210935
```

说明部分 query 依赖更多局部 visual evidence，小 M 会导致 fine-grained ranking 变差。

---

### 8.3 bits 控制 Ranking Fidelity

Day 5 bits sweep 显示：

| Setting | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Compression Ratio |
|---|---:|---:|---:|---:|---:|
| PQ-b2 | 0.266667 | 0.063148 | 0.105743 | 0.009247 | 512× |
| PQ-b4 | 0.266667 | 0.088929 | 0.125460 | 0.018494 | 256× |

结论：

```text
bits 从 4 降到 2 可进一步降低 index size，但会明显损害 MRR@10 和 nDCG@10。
```

因此 bits 控制的是 fine-grained similarity ranking fidelity，而不是当前设置下的 Recall@10。

---

## 9. Failure Case 总结

Day 5 归纳了四类失败案例。

| Failure Type | Representative Query | Main Cause | Interpretation |
|---|---|---|---|
| small_N_or_coarse_miss | q005–q030 中多数 query | gold page 未进入 top-10 candidate pool | N 控制 recall ceiling |
| small_M_failure | q004 | 局部 token evidence 不足 | M 控制 fine-grained evidence |
| quantization_ranking_distortion | q002, q025, q004 | quantization noise 改变排序 | bits 控制 ranking fidelity |
| large_budget_still_failure | best-quality 配置仍 miss 的 query | 表示能力或 coarse retrieval 不足 | 非预算因素也会限制性能 |

---

## 10. 本周论文级主张草稿

本周实验支持以下论文级主张：

```text
在 PCB 文档页面检索任务中，Budgeted Multi-vector Retrieval 可以通过联合控制候选页数 N、页面 token 数 M 和向量量化精度 bits，在显著降低索引体积的同时保持具有竞争力的检索质量。实验表明，N 主要决定 coarse recall ceiling，M 决定 late interaction 阶段可用的局部视觉证据，而 bits 决定量化后的 fine-grained ranking fidelity。三者共同形成清晰的质量–成本 Pareto frontier。
```

英文草稿：

```text
In PCB document-page retrieval, Budgeted Multi-vector Retrieval jointly controls the candidate-page budget N, the retained visual-token budget M, and the quantization precision bits. This budget triplet substantially reduces the estimated index size while preserving competitive retrieval quality. Our analysis shows that N determines the coarse-stage recall ceiling, M controls the amount of fine-grained visual evidence available to late interaction, and bits governs the ranking fidelity under vector quantization. Together, these dimensions form a clear quality-cost Pareto frontier.
```

---

## 11. 本周结论

Week 6 已完成预算化多向量检索主实验闭环。实验覆盖了 15 组 joint budget 配置，并额外完成 bits sensitivity 分析。结果显示，当前 Recall@10 上限由 N=10 的 coarse candidate pool 决定，M 和 bits 主要影响排序质量，即 MRR@10 和 nDCG@10。

在存储成本方面，PQ 系列压缩将 estimated index size 从 MB 级降低到 0.006–0.018 MB 区间，约实现 256× 的压缩倍率。最高质量点为 M24 + IVF+OPQ+PQ，最佳 trade-off 点为 M24 + PQ，最低成本与最快 budgeted 点为 M8 + IVF+OPQ+PQ。

本周结果已经形成论文主实验章节所需的核心材料，包括主结果表、三张核心图、Pareto frontier、预算三元组分析和失败案例证据。
