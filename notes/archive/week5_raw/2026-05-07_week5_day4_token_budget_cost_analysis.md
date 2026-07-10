# Week 5 Day 4 Token Budget Cost Analysis Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Day:** Day 4  
**Date:** 2026-05-07  
**Experiment Name:** Index Size, Latency, and Quality-Cost Analysis under Different Token Budgets  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是基于 Day 3 已完成的不同 token budget 检索实验，进一步统计不同 M 下的索引体积、向量数量、检索时延，并绘制质量–成本曲线。

本日重点包括：

1. 统计不同 M 下的索引大小；
2. 统计不同 M 下的总向量数；
3. 统计不同 M 下的平均每页 token 数；
4. 计算相对 full-token setting 的压缩比例；
5. 汇总 reranking latency；
6. 合并检索质量指标与成本指标；
7. 绘制 index size curve；
8. 绘制 quality vs index size 曲线；
9. 绘制 quality vs latency 曲线；
10. 分析当前最优 quality-cost trade-off 点。

---

## 2. 实验背景

Day 3 已完成不同 token budget M 下的正式 C2F reranking 实验。

本日实验直接复用 Day 3 的输出结果，不重新运行检索流程。

当前实验设置如下：

| 项目 | 设置 |
|---|---|
| Page count | 101 |
| Query count | 30 |
| Candidate count | 300 |
| Avg candidates/query | 10 |
| Fixed candidate budget | N=10 |
| Embedding dim | 512 |
| Full-token setting | M49 |
| Token budgets | M8, M16, M24, M32, M49 |

说明：

- 当前每页原始 page token 数为 49；
- 因此 M49 是 full-token setting；
- 原计划中的 M64、M128、M256 不适用于当前 embedding shape；
- 今日主要比较 M8、M16、M24、M32、M49 的成本和质量变化。

---

## 3. 今日输入文件

### 3.1 Day 3 Metrics 文件

今日使用 Day 3 生成的统一评测结果：

```text
results\budgeted\token_selection\summary\token_budget_metrics.csv
```

该文件包含不同 M 下的：

- Recall@1；
- Recall@5；
- Recall@10；
- MRR@10；
- nDCG@10；
- run file path；
- latency 信息。

---

### 3.2 Day 3 Latency 文件

今日使用 Day 3 生成的 reranking latency summary：

```text
results\budgeted\token_selection\summary\token_budget_day3_latency_by_M.csv
```

该文件包含：

- Query Count；
- Total Candidates；
- Avg Candidates / Query；
- Rerank Time Seconds；
- Per-query Latency ms；
- Run File；
- Validation File。

---

### 3.3 Compressed Page Embeddings

今日统计以下 compressed page embedding 目录：

```text
artifacts\embeddings\token_selection\pages_M8
artifacts\embeddings\token_selection\pages_M16
artifacts\embeddings\token_selection\pages_M24
artifacts\embeddings\token_selection\pages_M32
artifacts\embeddings\token_selection\pages_M49
```

---

## 4. 今日执行流程

### 4.1 检查 Day 3 输入文件

确认以下文件存在：

```bat
dir results\budgeted\token_selection\summary\token_budget_metrics.csv
dir results\budgeted\token_selection\summary\token_budget_day3_latency_by_M.csv
```

检查结果：

| 文件 | 状态 |
|---|---|
| `token_budget_metrics.csv` | Exists |
| `token_budget_day3_latency_by_M.csv` | Exists |

说明 Day 3 的质量指标和时延指标可以正常用于 Day 4 分析。

---

### 4.2 检查 compressed embedding 目录

检查以下目录：

```bat
dir artifacts\embeddings\token_selection\pages_M8
dir artifacts\embeddings\token_selection\pages_M16
dir artifacts\embeddings\token_selection\pages_M24
dir artifacts\embeddings\token_selection\pages_M32
dir artifacts\embeddings\token_selection\pages_M49
```

检查结果显示，每个 M 下均包含 101 个 page embedding 文件。

| M | 文件数量 | 状态 |
|---:|---:|---|
| 8 | 101 | Passed |
| 16 | 101 | Passed |
| 24 | 101 | Passed |
| 32 | 101 | Passed |
| 49 | 101 | Passed |

说明：

1. 不同 M 的 page embedding 数量一致；
2. Day 4 的 index size 统计具有可比性；
3. 所有 M 均覆盖完整页面集合。

---

### 4.3 创建 Day 4 输出目录

执行：

```bat
if not exist results\budgeted\token_selection\day4_cost_analysis mkdir results\budgeted\token_selection\day4_cost_analysis
if not exist results\budgeted\token_selection\figures mkdir results\budgeted\token_selection\figures
```

输出目录：

```text
results\budgeted\token_selection\day4_cost_analysis
results\budgeted\token_selection\figures
```

---

### 4.4 运行 Day 4 分析脚本

执行：

```bat
python scripts\analysis\analyze_token_budget_day4.py
```

终端输出：

```text
[Done] Day 4 token budget cost analysis completed.
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_index_size_stats.csv
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_latency_stats.csv
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_quality_cost_table.csv
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_token_budget_cost_analysis.xlsx
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_index_size_stats.md
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_latency_stats.md
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_quality_cost_table.md
[Output] results\budgeted\token_selection\day4_cost_analysis\day4_cost_analysis_summary.md
[Figure] results\budgeted\token_selection\figures\day4_index_size_curve.png
[Figure] results\budgeted\token_selection\figures\day4_index_size_curve.pdf
[Figure] results\budgeted\token_selection\figures\day4_index_reduction_curve.png
[Figure] results\budgeted\token_selection\figures\day4_index_reduction_curve.pdf
[Figure] results\budgeted\token_selection\figures\day4_avg_tokens_curve.png
[Figure] results\budgeted\token_selection\figures\day4_avg_tokens_curve.pdf
[Figure] results\budgeted\token_selection\figures\day4_quality_vs_index_size.png
[Figure] results\budgeted\token_selection\figures\day4_quality_vs_index_size.pdf
[Figure] results\budgeted\token_selection\figures\day4_quality_vs_latency.png
[Figure] results\budgeted\token_selection\figures\day4_quality_vs_latency.pdf
```

说明 Day 4 成本分析脚本执行成功，统计表和图像文件均已生成。

---

## 5. 今日生成文件

### 5.1 统计表文件

今日生成以下统计表：

| 文件 | 路径 |
|---|---|
| Index size stats | `results\budgeted\token_selection\day4_cost_analysis\day4_index_size_stats.csv` |
| Latency stats | `results\budgeted\token_selection\day4_cost_analysis\day4_latency_stats.csv` |
| Quality-cost table | `results\budgeted\token_selection\day4_cost_analysis\day4_quality_cost_table.csv` |
| Excel summary | `results\budgeted\token_selection\day4_cost_analysis\day4_token_budget_cost_analysis.xlsx` |

---

### 5.2 Markdown 汇总文件

今日生成以下 Markdown 文件：

| 文件 | 路径 |
|---|---|
| Index size markdown | `results\budgeted\token_selection\day4_cost_analysis\day4_index_size_stats.md` |
| Latency markdown | `results\budgeted\token_selection\day4_cost_analysis\day4_latency_stats.md` |
| Quality-cost markdown | `results\budgeted\token_selection\day4_cost_analysis\day4_quality_cost_table.md` |
| Cost analysis summary | `results\budgeted\token_selection\day4_cost_analysis\day4_cost_analysis_summary.md` |

---

### 5.3 图像文件

今日生成以下曲线图：

| 图像 | 路径 |
|---|---|
| Index size curve PNG | `results\budgeted\token_selection\figures\day4_index_size_curve.png` |
| Index size curve PDF | `results\budgeted\token_selection\figures\day4_index_size_curve.pdf` |
| Index reduction curve PNG | `results\budgeted\token_selection\figures\day4_index_reduction_curve.png` |
| Index reduction curve PDF | `results\budgeted\token_selection\figures\day4_index_reduction_curve.pdf` |
| Avg tokens curve PNG | `results\budgeted\token_selection\figures\day4_avg_tokens_curve.png` |
| Avg tokens curve PDF | `results\budgeted\token_selection\figures\day4_avg_tokens_curve.pdf` |
| Quality vs index size PNG | `results\budgeted\token_selection\figures\day4_quality_vs_index_size.png` |
| Quality vs index size PDF | `results\budgeted\token_selection\figures\day4_quality_vs_index_size.pdf` |
| Quality vs latency PNG | `results\budgeted\token_selection\figures\day4_quality_vs_latency.png` |
| Quality vs latency PDF | `results\budgeted\token_selection\figures\day4_quality_vs_latency.pdf` |

---

## 6. Index Size 统计结果

### 6.1 不同 M 下的索引体积

今日统计得到以下结果：

| Setting | M | Num Pages | Total Vectors | Avg Tokens/Page | Payload Size MB | File Size MB | Payload Reduction vs Full |
|---|---:|---:|---:|---:|---:|---:|---:|
| M8 | 8 | 101 | 808 | 8.00 | 1.5781 | 1.5905 | 83.67% |
| M16 | 16 | 101 | 1616 | 16.00 | 3.1563 | 3.1686 | 67.35% |
| M24 | 24 | 101 | 2424 | 24.00 | 4.7344 | 4.7467 | 51.02% |
| M32 | 32 | 101 | 3232 | 32.00 | 6.3125 | 6.3248 | 34.69% |
| M49 | 49 | 101 | 4949 | 49.00 | 9.6660 | 9.6783 | 0.00% |

---

### 6.2 Index Size 结果观察

从 M49 降到 M8：

- Avg Tokens/Page 从 49 降到 8；
- Total Vectors 从 4949 降到 808；
- Payload Size 从 9.6660 MB 降到 1.5781 MB；
- Payload Reduction 达到 83.67%。

从 M49 降到 M16：

- Avg Tokens/Page 从 49 降到 16；
- Total Vectors 从 4949 降到 1616；
- Payload Size 从 9.6660 MB 降到 3.1563 MB；
- Payload Reduction 达到 67.35%。

从 M49 降到 M24：

- Avg Tokens/Page 从 49 降到 24；
- Total Vectors 从 4949 降到 2424；
- Payload Reduction 达到 51.02%。

从 M49 降到 M32：

- Avg Tokens/Page 从 49 降到 32；
- Total Vectors 从 4949 降到 3232；
- Payload Reduction 达到 34.69%。

总体上，index size 与 M 基本呈线性关系。M 越小，平均每页 tokens 越少，总向量数和 payload size 越低。

---

## 7. Latency 统计结果

### 7.1 不同 M 下的 reranking latency

今日统计得到以下 latency 结果：

| Method | M | Query Count | Total Candidates | Avg Candidates / Query | Rerank Time Seconds | Per-query Latency ms |
|---|---:|---:|---:|---:|---:|---:|
| c2f_N10_M8 | 8 | 30 | 300 | 10 | 0.0607 | 2.0249 |
| c2f_N10_M16 | 16 | 30 | 300 | 10 | 0.0491 | 1.6379 |
| c2f_N10_M24 | 24 | 30 | 300 | 10 | 0.0505 | 1.6846 |
| c2f_N10_M32 | 32 | 30 | 300 | 10 | 0.0545 | 1.8168 |
| c2f_N10_M49 | 49 | 30 | 300 | 10 | 0.0716 | 2.3857 |

---

### 7.2 Latency 结果观察

从 latency 看：

1. M49 的 per-query latency 最高，为 2.3857 ms/query；
2. M16 的 per-query latency 最低，为 1.6379 ms/query；
3. M24 的 latency 为 1.6846 ms/query，接近 M16；
4. M32 的 latency 为 1.8168 ms/query；
5. M8 的 latency 为 2.0249 ms/query，高于 M16/M24/M32。

M8 的 latency 没有最低，可能与以下因素有关：

- 当前 query 数只有 30，计时样本较小；
- 每个 query 只有 10 个候选，整体耗时非常短；
- Python 文件读取、缓存状态、循环开销对毫秒级结果影响明显；
- 小规模计时中，token 数减少不一定完全线性反映在 wall-clock latency 上。

因此，latency 趋势可以作为参考，但不应过度解释细微差异。更稳定的结论是：M49 作为 full-token setting 计算成本最高，而 M16/M24 在当前设置下具有更好的时延表现。

---

## 8. Quality-Cost 综合结果

### 8.1 质量与成本合并表

Day 4 合并 Day 3 的 retrieval metrics、index size 和 latency 后，得到以下 quality-cost 表：

| M | Avg Tokens/Page | Total Vectors | Payload Size MB | Payload Reduction | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 8.00 | 808 | 1.5781 | 83.67% | 0.2667 | 0.0907 | 0.1249 | 2.0249 |
| 16 | 16.00 | 1616 | 3.1563 | 67.35% | 0.2667 | 0.0901 | 0.1242 | 1.6379 |
| 24 | 24.00 | 2424 | 4.7344 | 51.02% | 0.2667 | 0.0754 | 0.1145 | 1.6846 |
| 32 | 32.00 | 3232 | 6.3125 | 34.69% | 0.2667 | 0.0465 | 0.0920 | 1.8168 |
| 49 | 49.00 | 4949 | 9.6660 | 0.00% | 0.2667 | 0.0628 | 0.1033 | 2.3857 |

---

### 8.2 质量保持情况

不同 M 下 Recall@10 均为：

```text
0.2667
```

这说明：

1. 在固定 N=10 的 reranking 设置下，减少 page tokens 没有降低 top-10 命中能力；
2. 即使 M8 只保留 8 个 tokens，仍保持与 M49 相同的 Recall@10；
3. 当前数据中，token budget 对 Recall@10 的影响不明显；
4. 质量变化主要体现在 MRR@10 和 nDCG@10 上，也就是排序质量而非 top-10 覆盖能力。

---

### 8.3 排序质量变化

不同 M 下的 MRR@10 和 nDCG@10 如下：

| M | MRR@10 | nDCG@10 |
|---:|---:|---:|
| 8 | 0.0907 | 0.1249 |
| 16 | 0.0901 | 0.1242 |
| 24 | 0.0754 | 0.1145 |
| 32 | 0.0465 | 0.0920 |
| 49 | 0.0628 | 0.1033 |

观察：

1. M8 的 MRR@10 和 nDCG@10 最高；
2. M16 与 M8 非常接近；
3. M24 仍高于 M49；
4. M32 低于 M49，是当前结果中排序质量最低的配置；
5. M49 并不是当前数据下排序质量最优的设置。

这说明 norm-based token selection 在当前数据中可能不仅降低了成本，还在部分 M 下产生了排序去噪效果。

---

## 9. 图像结果说明

### 9.1 Average Tokens Curve

图像文件：

```text
results\budgeted\token_selection\figures\day4_avg_tokens_curve.png
```

该图显示：

- 横轴为 Token Budget M；
- 纵轴为 Avg Tokens/Page；
- Avg Tokens/Page 随 M 线性增长；
- M8、M16、M24、M32、M49 分别对应平均每页 8、16、24、32、49 个 tokens。

该图验证了 token selection 的基本行为：每页实际保留 token 数与设定 M 一致。

---

### 9.2 Index Size Curve

图像文件：

```text
results\budgeted\token_selection\figures\day4_index_size_curve.png
```

该图显示：

- 横轴为 Token Budget M；
- 纵轴为 Index Size MB；
- Payload Size MB 和 File Size MB 基本重合；
- index size 随 M 增大近似线性增加。

观察：

- M8 index size 最小，约 1.58 MB；
- M49 index size 最大，约 9.67 MB；
- 从 M49 降到 M16 时，索引体积显著下降。

---

### 9.3 Index Reduction Curve

图像文件：

```text
results\budgeted\token_selection\figures\day4_index_reduction_curve.png
```

该图显示：

- 横轴为 Token Budget M；
- 纵轴为 Payload Reduction vs Full；
- M 越小，相对 M49 的压缩比例越高。

关键结果：

| M | Payload Reduction vs Full |
|---:|---:|
| 8 | 83.67% |
| 16 | 67.35% |
| 24 | 51.02% |
| 32 | 34.69% |
| 49 | 0.00% |

说明 token selection 能显著降低 index storage cost。

---

### 9.4 Quality vs Index Size Curve

图像文件：

```text
results\budgeted\token_selection\figures\day4_quality_vs_index_size.png
```

该图显示：

- 横轴为 Index Payload Size MB；
- 纵轴为 Retrieval Quality；
- 曲线包括 Recall@10、nDCG@10 和 MRR@10。

观察：

1. Recall@10 基本保持水平，不随 index size 增大而提升；
2. nDCG@10 在 M8/M16 处最高；
3. MRR@10 在 M8/M16 处最高；
4. M49 虽然 index size 最大，但排序质量并不是最高；
5. M16 位于较小 index size 与较高质量的优良区间。

该图是今日最重要的质量–成本对比图之一。

---

### 9.5 Quality vs Latency Curve

图像文件：

```text
results\budgeted\token_selection\figures\day4_quality_vs_latency.png
```

该图显示：

- 横轴为 Per-query Latency ms；
- 纵轴为 Retrieval Quality；
- 曲线包括 Recall@10、nDCG@10 和 MRR@10。

观察：

1. Recall@10 在所有 M 下保持 0.2667；
2. M16 latency 最低，同时 nDCG@10 和 MRR@10 接近最高；
3. M49 latency 最高，但质量指标不是最高；
4. M8 质量最高，但 latency 高于 M16；
5. M32 的 latency 中等，但排序质量最低。

因此，从 quality-latency trade-off 看，M16 是当前最稳健的配置。

---

## 10. Trade-off 分析

### 10.1 最小索引配置

最小索引配置为：

```text
M8
```

M8 的结果：

| Metric | Value |
|---|---:|
| Avg Tokens/Page | 8 |
| Total Vectors | 808 |
| Payload Size MB | 1.5781 |
| Payload Reduction vs Full | 83.67% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0907 |
| nDCG@10 | 0.1249 |
| Latency ms/query | 2.0249 |

M8 的特点：

- index size 最小；
- payload reduction 最大；
- MRR@10 和 nDCG@10 最高；
- 但 latency 并不是最低。

M8 是最强压缩配置，也是当前结果中质量最高的配置。但由于 latency 不如 M16，综合效率上 M16 更稳。

---

### 10.2 最快 reranking 配置

最快 reranking 配置为：

```text
M16
```

M16 的结果：

| Metric | Value |
|---|---:|
| Avg Tokens/Page | 16 |
| Total Vectors | 1616 |
| Payload Size MB | 3.1563 |
| Payload Reduction vs Full | 67.35% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0901 |
| nDCG@10 | 0.1242 |
| Latency ms/query | 1.6379 |

M16 的特点：

- latency 最低；
- index size 比 M49 减少 67.35%；
- Recall@10 与 M49 持平；
- MRR@10 和 nDCG@10 明显高于 M49；
- 排序质量接近 M8。

因此，M16 是当前最优 quality-cost trade-off 配置。

---

### 10.3 Full-token reference

Full-token setting 为：

```text
M49
```

M49 的结果：

| Metric | Value |
|---|---:|
| Avg Tokens/Page | 49 |
| Total Vectors | 4949 |
| Payload Size MB | 9.6660 |
| Payload Reduction vs Full | 0.00% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0628 |
| nDCG@10 | 0.1033 |
| Latency ms/query | 2.3857 |

M49 作为 full-token baseline，成本最高，但排序质量并不是最优。这说明当前 norm-based token selection 可能在一定程度上过滤掉了低价值 tokens 或噪声 tokens。

---

### 10.4 M32 的异常表现

M32 的结果：

| Metric | Value |
|---|---:|
| Avg Tokens/Page | 32 |
| Total Vectors | 3232 |
| Payload Size MB | 6.3125 |
| Payload Reduction vs Full | 34.69% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0465 |
| nDCG@10 | 0.0920 |
| Latency ms/query | 1.8168 |

M32 的 Recall@10 与其他 M 一致，但 MRR@10 和 nDCG@10 最低。

可能原因：

1. M32 保留了更多 tokens，但新增 tokens 不一定对当前 query 有帮助；
2. late interaction scoring 中，额外 tokens 可能改变最大相似度结构；
3. norm-based selection 是 query-independent 方法，不保证每个 M 都单调提升排序质量；
4. 当前 query 数为 30，少数 query 的排序变化会显著影响 MRR 和 nDCG。

该现象说明：更多 tokens 并不一定带来更好的排序质量。

---

## 11. 成本下降与质量变化总结

### 11.1 从 M49 到 M16

从 M49 降到 M16：

| 指标 | M49 | M16 | 变化 |
|---|---:|---:|---:|
| Avg Tokens/Page | 49 | 16 | 减少 67.35% |
| Total Vectors | 4949 | 1616 | 减少 67.35% |
| Payload Size MB | 9.6660 | 3.1563 | 减少 67.35% |
| Recall@10 | 0.2667 | 0.2667 | 持平 |
| MRR@10 | 0.0628 | 0.0901 | 提升 |
| nDCG@10 | 0.1033 | 0.1242 | 提升 |
| Latency ms/query | 2.3857 | 1.6379 | 降低 |

结论：

```text
M16 在显著降低 index size 和 latency 的同时，没有降低 Recall@10，并且提升了排序质量。
```

---

### 11.2 从 M49 到 M8

从 M49 降到 M8：

| 指标 | M49 | M8 | 变化 |
|---|---:|---:|---:|
| Avg Tokens/Page | 49 | 8 | 减少 83.67% |
| Total Vectors | 4949 | 808 | 减少 83.67% |
| Payload Size MB | 9.6660 | 1.5781 | 减少 83.67% |
| Recall@10 | 0.2667 | 0.2667 | 持平 |
| MRR@10 | 0.0628 | 0.0907 | 提升 |
| nDCG@10 | 0.1033 | 0.1249 | 提升 |
| Latency ms/query | 2.3857 | 2.0249 | 降低 |

结论：

```text
M8 是最强压缩配置，并且在当前结果中质量指标最高，但 latency 不是最低。
```

---

### 11.3 从 M49 到 M24

从 M49 降到 M24：

| 指标 | M49 | M24 | 变化 |
|---|---:|---:|---:|
| Avg Tokens/Page | 49 | 24 | 减少 51.02% |
| Total Vectors | 4949 | 2424 | 减少 51.02% |
| Payload Size MB | 9.6660 | 4.7344 | 减少 51.02% |
| Recall@10 | 0.2667 | 0.2667 | 持平 |
| MRR@10 | 0.0628 | 0.0754 | 提升 |
| nDCG@10 | 0.1033 | 0.1145 | 提升 |
| Latency ms/query | 2.3857 | 1.6846 | 降低 |

结论：

```text
M24 是一个较保守的压缩配置，能减少约一半 index size，同时保持 Recall@10 并提升排序质量。
```

---

## 12. 当前最优配置判断

综合 index size、latency、Recall@10、MRR@10 和 nDCG@10，当前最优 trade-off 配置为：

```text
M16
```

理由：

1. 相比 M49，M16 的 payload size 减少 67.35%；
2. M16 的 Recall@10 与 M49 持平；
3. M16 的 MRR@10 高于 M49；
4. M16 的 nDCG@10 高于 M49；
5. M16 是所有配置中 reranking latency 最低的；
6. M16 的质量指标与 M8 非常接近，但速度更快；
7. M16 在质量、索引大小和延迟之间最均衡。

M8 适合作为最大压缩配置，M24 适合作为保守压缩配置，M16 是当前推荐配置。

---

## 13. 今日关键发现

今日实验得到以下关键发现：

1. 不同 M 下 compressed page embeddings 均覆盖 101 个页面；
2. index size 与 token budget M 基本呈线性关系；
3. M8 将 payload size 从 9.6660 MB 降至 1.5781 MB，缩减 83.67%；
4. M16 将 payload size 从 9.6660 MB 降至 3.1563 MB，缩减 67.35%；
5. M24 将 payload size 从 9.6660 MB 降至 4.7344 MB，缩减 51.02%；
6. 所有 M 下 Recall@10 均保持 0.2667；
7. M8 和 M16 的 MRR@10 与 nDCG@10 高于 M49；
8. M16 是当前 latency 最低的配置；
9. M49 成本最高，但排序质量不是最优；
10. Norm-based token selection 在当前数据集上具有明显的质量–效率优势。

---

## 14. 今日验收情况

| 验收项 | 状态 |
|---|---|
| 索引体积统计表已生成 | Completed |
| 时延统计表已生成 | Completed |
| 质量–成本综合表已生成 | Completed |
| Excel 汇总表已生成 | Completed |
| Index size curve 已生成 | Completed |
| Index reduction curve 已生成 | Completed |
| Avg tokens curve 已生成 | Completed |
| Quality vs index size curve 已生成 | Completed |
| Quality vs latency curve 已生成 | Completed |
| Cost analysis summary 已生成 | Completed |
| 能定量说明不同 M 的成本下降 | Completed |
| 能定量说明不同 M 的质量变化 | Completed |
| 当前最优 trade-off 配置已判断 | Completed |

---

## 15. 今日结论

Week 5 Day 4 已完成不同 token budget M 下的索引体积、检索时延和质量–成本关系分析。

今日结果表明，token selection 能够显著降低 index size。以 M49 作为 full-token reference，M16 能将 payload size 从 9.6660 MB 降至 3.1563 MB，减少 67.35%；同时 Recall@10 保持 0.2667 不变，MRR@10 从 0.0628 提升到 0.0901，nDCG@10 从 0.1033 提升到 0.1242，per-query latency 也从 2.3857 ms 降至 1.6379 ms。

M8 虽然具有最小 index size 和最高排序质量指标，但 latency 不如 M16。M24 是较保守的压缩配置，能减少约 51.02% 的 payload size 并保持较好质量。M32 在当前结果中排序质量较低，说明 token 数增加并不必然带来更好的 late interaction 排序效果。

最终判断：

> Day 4 验收通过。当前已经能够定量说明：将每页 token 数从 full-token M49 降到 M16 时，索引体积减少约 67.35%，检索时延降低，同时 Recall@10 不下降，MRR@10 和 nDCG@10 反而提升。因此 M16 是当前实验中最优的 quality-cost trade-off 配置。
