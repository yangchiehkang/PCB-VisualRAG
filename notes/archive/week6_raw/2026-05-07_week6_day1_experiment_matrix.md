# Week 6 Day 1 Joint Budget Experiment Matrix

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 1  
**Date:** 2026-05-07  
**Experiment Name:** Joint Budget Matrix Design for Quantized Budgeted Multi-vector Retrieval  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 1 的目标是根据 Week 4 和 Week 5 的实验结果，收缩联合 budget 实验空间，并确定 Week 6 的代表性实验矩阵。

Week 6 的核心预算三元组定义为：

```text
Budget = (N, M, Compression)
```

其中：

- N 表示进入 reranking 的候选页面数量；
- M 表示每个页面保留的 page token 数；
- Compression 表示向量压缩方式，包括 None、PQ、OPQ+PQ、IVF+PQ、IVF+OPQ+PQ。

本日重点不是穷举所有组合，而是选择少量有代表性的 budget points，覆盖低预算、中等预算和高质量预算区间。

---

## 2. 前置实验约束

### 2.1 N 维度约束

Week 4 的 coarse-to-fine 实验显示，当前实际可用的 coarse candidate 文件为：

```text
artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
```

该文件统计如下：

| 项目 | 数量 |
|---|---:|
| Query Count | 30 |
| Candidate Rows | 300 |
| Avg Candidates / Query | 10 |

因此，虽然原始 Week 6 计划中给出了 N=20、N=50、N=100 的模板，但当前真实实验环境中只稳定支持：

```text
N = 10
```

本周先固定 N=10，将重点放在 token budget M 与 vector compression 的联合分析上。

---

### 2.2 M 维度约束

Week 5 已确认当前页面 full multi-vector embedding 的 shape 为：

```text
(49, 512)
```

因此每页原始 token 数为：

```text
L = 49
```

这意味着原计划中的 M64、M128 不适用于当前实验。当前可用的 token budget 为：

| Setting | M | Keep Ratio | Redundancy Ratio |
|---|---:|---:|---:|
| M8 | 8 | 16.33% | 83.67% |
| M16 | 16 | 32.65% | 67.35% |
| M24 | 24 | 48.98% | 51.02% |
| M32 | 32 | 65.31% | 34.69% |
| M49 | 49 | 100.00% | 0.00% |

Week 5 结果显示：

- M8 是极致轻量点；
- M16 是最佳 quality-cost trade-off 点；
- M24 是高质量 / 保守压缩点；
- M32 排序质量低于 M49，不适合作为 Week 6 主代表点；
- M49 是 full-token reference。

---

## 3. 代表性 N, M 配置选择

根据 Week 4 和 Week 5 的真实实验结果，Week 6 Day 1 选定以下代表配置：

| Budget Level | N | M | 说明 | 选择理由 |
|---|---:|---:|---|---|
| Low-budget | 10 | 8 | 极致轻量点 | 只保留 16.33% tokens，payload 减少 83.67%，用于测试极限压缩边界 |
| Mid-budget | 10 | 16 | 最佳 trade-off 点 | payload 减少 67.35%，Recall@10 不下降，MRR@10 和 nDCG@10 高于 M49，latency 最低 |
| High-budget | 10 | 24 | 高质量 / 保守压缩点 | 保留接近一半 tokens，payload 减少 51.02%，排序质量仍高于 M49 |
| Reference | 10 | 49 | Full-token reference | 不进行 token pruning，用于衡量预算化方法相对 full-token setting 的变化 |

Week 6 的主实验矩阵只使用前三个预算点：

```text
(N, M) ∈ {(10, 8), (10, 16), (10, 24)}
```

M49 作为 reference 单独保留，不纳入主矩阵的压缩组合，以避免组合数过多。

---

## 4. Compression 设置

对每个代表性 N, M 配置，叠加以下 compression 方法：

| Compression | 说明 |
|---|---|
| None | 不进行向量量化，作为该 N, M 下的未压缩 reference |
| PQ | 基础 Product Quantization，用于降低向量存储成本 |
| OPQ + PQ | 在 PQ 前加入 Optimized Product Quantization 旋转变换，以降低量化误差 |
| IVF + PQ | 使用倒排结构进行 coarse quantization，再在 list 内使用 PQ |
| IVF + OPQ + PQ | 结合 IVF、OPQ 和 PQ，用于同时追求压缩率与检索速度 |

因此主实验总组合数为：

```text
3 budget levels × 5 compression settings = 15 configurations
```

该数量符合 Week 6 Day 1 对实验规模的要求：控制在 9–15 组左右，避免组合爆炸。

---

## 5. Week 6 主实验矩阵

| Budget Level | N | M | Compression | Run Name |
|---|---:|---:|---|---|
| Low-budget | 10 | 8 | None | `w6_N10_M8_none` |
| Low-budget | 10 | 8 | PQ | `w6_N10_M8_pq` |
| Low-budget | 10 | 8 | OPQ+PQ | `w6_N10_M8_opq_pq` |
| Low-budget | 10 | 8 | IVF+PQ | `w6_N10_M8_ivf_pq` |
| Low-budget | 10 | 8 | IVF+OPQ+PQ | `w6_N10_M8_ivf_opq_pq` |
| Mid-budget | 10 | 16 | None | `w6_N10_M16_none` |
| Mid-budget | 10 | 16 | PQ | `w6_N10_M16_pq` |
| Mid-budget | 10 | 16 | OPQ+PQ | `w6_N10_M16_opq_pq` |
| Mid-budget | 10 | 16 | IVF+PQ | `w6_N10_M16_ivf_pq` |
| Mid-budget | 10 | 16 | IVF+OPQ+PQ | `w6_N10_M16_ivf_opq_pq` |
| High-budget | 10 | 24 | None | `w6_N10_M24_none` |
| High-budget | 10 | 24 | PQ | `w6_N10_M24_pq` |
| High-budget | 10 | 24 | OPQ+PQ | `w6_N10_M24_opq_pq` |
| High-budget | 10 | 24 | IVF+PQ | `w6_N10_M24_ivf_pq` |
| High-budget | 10 | 24 | IVF+OPQ+PQ | `w6_N10_M24_ivf_opq_pq` |

---

## 6. Reference 配置

除主矩阵外，保留以下 reference：

| Reference Type | N | M | Compression | 说明 |
|---|---:|---:|---|---|
| Full-token C2F reference | 10 | 49 | None | Week 5 的 M49，作为 full-token setting |
| Full MV system reference | N/A | full | None | Week 3 的 Full Multi-vector baseline，作为系统级参考 |

当前 reference 指标如下：

| Method | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---:|---:|---:|---:|---:|
| Full MV | 0.1333 | 0.0644 | 0.0807 | 9.6660 | N/A |
| C2F N10 M49 None | 0.2667 | 0.0628 | 0.1033 | 9.6660 | 2.3857 |

说明：

- Full MV 与 C2F N10 M49 不是完全相同 pipeline；
- Week 6 的主要内部 reference 是 C2F N10 M49 None；
- Full MV 用作系统级高质量参考。

---

## 7. 本周统一评价指标

Week 6 所有配置统一记录以下指标：

| 指标 | 说明 |
|---|---|
| Recall@10 | top-10 命中能力 |
| MRR@10 | 相关页面排名靠前程度 |
| nDCG@10 | 排序质量 |
| Index Size MB | 压缩后索引体积 |
| Latency ms/query | 平均每个 query 的检索或 reranking 时延 |

后续如果压缩索引支持更细统计，也记录：

| 补充指标 | 说明 |
|---|---|
| Compression Ratio | 相对未压缩 index 的大小下降比例 |
| Code Size | PQ code size |
| Bits / subvector | PQ 每个子空间的编码位数 |
| nlist | IVF 聚类中心数量 |
| nprobe | IVF 查询时搜索的 list 数量 |
| Build Time | 压缩索引构建时间 |

---

## 8. 本周 Run 命名规范

统一 run name 格式：

```text
w6_N{N}_M{M}_{compression}
```

示例：

```text
w6_N10_M8_none
w6_N10_M8_pq
w6_N10_M8_opq_pq
w6_N10_M8_ivf_pq
w6_N10_M8_ivf_opq_pq
```

推荐输出路径：

```text
results/budgeted/joint_compression/runs/{run_name}_run.tsv
results/budgeted/joint_compression/scores/{run_name}_scores.csv
results/budgeted/joint_compression/metrics/{run_name}_metrics.json
results/budgeted/joint_compression/index_stats/{run_name}_index_stats.json
results/budgeted/joint_compression/latency/{run_name}_latency.json
```

统一 summary 输出：

```text
results/budgeted/joint_compression/summary/week6_experiment_matrix.csv
results/budgeted/joint_compression/summary/week6_experiment_matrix.md
results/budgeted/joint_compression/summary/joint_budget_results.csv
results/budgeted/joint_compression/summary/joint_budget_results.xlsx
```

---

## 9. 今日明确不跑的配置

为控制实验规模，Day 1 明确暂不运行以下配置：

| 不跑配置 | 原因 |
|---|---|
| N=20, N=50, N=100 | 当前已有 coarse candidate 文件实际只支持 N=10 |
| M64, M128 | 当前每页 full token 数只有 49，M64/M128 超过有效 token 数 |
| M32 主矩阵压缩实验 | Week 5 中 M32 排序质量低于 M49，不适合作为代表性主点 |
| 全部 N × M × Compression 穷举 | 组合过多，不利于解释，也不符合 Week 6 收束目标 |

后续如果重新生成 top20/top50/top100 candidates，可扩展 N 维度实验。

---

## 10. 为什么这些点足以支撑主结论

当前选择的三个预算点覆盖了 Week 6 需要的低、中、高预算区间：

1. **N10 M8** 代表极致轻量点，测试最低 token budget 下叠加 compression 后的性能下界；
2. **N10 M16** 代表最佳 trade-off 点，是 Week 5 已验证的最优质量–成本折中；
3. **N10 M24** 代表高质量 / 保守压缩点，用于观察较高 token budget 下量化压缩是否仍能保持质量；
4. **N10 M49 None** 作为 full-token reference，用于衡量 token pruning 和 compression 的相对损失。

这组配置能够回答 Week 6 的核心问题：

> 在固定候选页面预算 N=10 的条件下，联合控制页面 token 数 M 和向量压缩方式，是否能够进一步降低 index size 与 latency，同时保持接近 full-token reranking 的检索质量？

虽然当前暂时无法完整覆盖 N 维度，但该实验已经形成：

```text
Budget = (N fixed, M, Compression)
```

的现实版本，为后续扩展到完整：

```text
Budget = (N, M, bits)
```

打下基础。

---

## 11. Day 1 验收情况

| 验收项 | 状态 |
|---|---|
| 代表性 N, M 配置已选定 | Completed |
| Compression 设置已确定 | Completed |
| 主实验矩阵已形成 | Completed |
| 组合数量已控制在 15 组 | Completed |
| 不跑配置及原因已说明 | Completed |
| Run 命名规范已确定 | Completed |
| 评价指标已固定 | Completed |

---

## 12. 今日结论

Week 6 Day 1 已完成联合 budget 实验矩阵设计。根据当前真实实验约束，本周固定候选页面预算 N=10，并选择 M8、M16、M24 作为低、中、高三个代表性 token budget 点。每个预算点叠加 None、PQ、OPQ+PQ、IVF+PQ 和 IVF+OPQ+PQ 五种 compression 设置，共形成 15 组主实验配置。

M49 不进入主实验矩阵，而作为 full-token reference 保留。该设计既符合 Week 6 控制实验规模的要求，也能够基于 Week 5 的真实结论继续推进 token pruning 与 vector compression 的联合质量–成本分析。

Week 6 Day 1 completed. Based on the real constraints from Week 4 and Week 5, the joint budget matrix was adapted from the original template. Since the current candidate file only supports N=10 and each page contains 49 tokens, the main experiment fixes N=10 and selects M8, M16, and M24 as low-, mid-, and high-budget representatives. Each budget point will be combined with five compression settings: None, PQ, OPQ+PQ, IVF+PQ, and IVF+OPQ+PQ, resulting in 15 main configurations. M49 is retained as the full-token C2F reference. This matrix controls experiment scale while preserving the ability to analyze the quality-cost trade-off of token pruning plus vector compression.

