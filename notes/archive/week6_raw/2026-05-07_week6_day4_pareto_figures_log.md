# Week 6 Day 4 实验日志：核心图绘制与 Pareto Frontier 分析

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 6  
**Day:** Day 4  
**Date:** 2026-05-07  
**Experiment:** Core Figure Generation and Pareto Frontier Analysis  
**Input Results:** Week 6 Day 3 Joint Budget Results  
**Quality Metric:** nDCG@10  
**Cost Metrics:** Index Size MB / Latency ms/query  
**Status:** Completed  

---

## 1. 今日目标

Week 6 Day 4 的目标是将 Day 3 生成的联合 budget 主结果表转化为论文主实验章节可用的核心图，并识别 Pareto frontier。

今日需要完成三类图：

```text
1. Quality vs. Index Size
2. Quality vs. Retrieval Latency
3. Pareto Frontier
```

其中质量指标使用：

```text
nDCG@10
```

成本指标分别使用：

```text
Index Size MB
Latency ms/query
```

今日还需要输出对应的 Pareto frontier 表格和图注草稿，为后续论文写作和结果讨论做准备。

---

## 2. 今日输入文件

Day 4 使用 Day 3 的主结果表作为输入：

```text
results/budgeted/joint_compression/summary/joint_budget_results.csv
```

同时使用 Day 3 代表点文件辅助标注关键配置：

```text
results/budgeted/joint_compression/day3_main/day3_representative_points.csv
```

输入结果覆盖 15 组配置：

```text
M ∈ {8, 16, 24}
Compression ∈ {None, PQ, OPQ+PQ, IVF+PQ, IVF+OPQ+PQ}
```

由于当前 candidate pool 固定为 top-10，所有实验均为：

```text
N = 10
```

---

## 3. 今日执行的脚本

今日运行的绘图脚本为：

```text
python scripts/visualization/plot_week6_day4_core_figures.py
```

该脚本完成以下工作：

- 读取 Day 3 主结果表；
- 清洗并标准化数值列；
- 以 nDCG@10 作为质量指标；
- 分别计算 index-size Pareto frontier 和 latency Pareto frontier；
- 绘制质量–索引大小图；
- 绘制质量–时延图；
- 绘制双面板 Pareto frontier 图；
- 输出 Pareto frontier 表；
- 输出带 Pareto flags 的完整结果表；
- 输出图注草稿。

---

## 4. 今日生成的核心图

### 4.1 Quality vs. Index Size

生成文件：

```text
results/budgeted/joint_compression/figures/quality_vs_index_size.pdf
results/budgeted/joint_compression/figures/quality_vs_index_size.png
results/budgeted/joint_compression/day4_figures/quality_vs_index_size.pdf
results/budgeted/joint_compression/day4_figures/quality_vs_index_size.png
```

该图横轴为：

```text
Index Size MB, log scale
```

纵轴为：

```text
nDCG@10
```

图中展示了不同压缩配置在存储成本和检索质量之间的关系。压缩配置集中在极低 index size 区域，说明 4-bit PQ 系列方法显著降低了 estimated index size。

---

### 4.2 Quality vs. Retrieval Latency

生成文件：

```text
results/budgeted/joint_compression/figures/quality_vs_latency.pdf
results/budgeted/joint_compression/figures/quality_vs_latency.png
results/budgeted/joint_compression/day4_figures/quality_vs_latency.pdf
results/budgeted/joint_compression/day4_figures/quality_vs_latency.png
```

该图横轴为：

```text
Latency ms/query
```

纵轴为：

```text
nDCG@10
```

该图用于观察检索质量与当前 reranking latency 之间的关系。由于当前 pipeline 使用 reconstructed embeddings 做 late interaction reranking，因此该 latency 主要反映兼容流程下的评分耗时，而不完全代表真实 IVF ANN 检索加速收益。

---

### 4.3 Pareto Frontier

生成文件：

```text
results/budgeted/joint_compression/figures/pareto_frontier.pdf
results/budgeted/joint_compression/figures/pareto_frontier.png
results/budgeted/joint_compression/day4_figures/pareto_frontier.pdf
results/budgeted/joint_compression/day4_figures/pareto_frontier.png
```

该图包含两个子图：

```text
Left:  Pareto Frontier: Quality vs. Index Size
Right: Pareto Frontier: Quality vs. Latency
```

图中黑色连线表示不可被同时更低成本和更高质量支配的 Pareto frontier 点。

---

## 5. 今日生成的分析表

### 5.1 Index Size Pareto Frontier

生成文件：

```text
results/budgeted/joint_compression/day4_figures/day4_pareto_index_size.csv
results/budgeted/joint_compression/day4_figures/day4_pareto_index_size.md
```

Index Size 维度上的 Pareto frontier 为：

| Run Name | N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| w6_N10_M8_ivf_opq_pq | 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.0553175 | 0.0990213 | 0.00616455 | 4.80393 |
| w6_N10_M16_ivf_opq_pq | 10 | 16 | IVF+OPQ+PQ | 0.266667 | 0.0779630 | 0.1162060 | 0.01232910 | 5.70052 |
| w6_N10_M24_ivf_opq_pq | 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.0956878 | 0.1295850 | 0.01849370 | 5.40662 |

观察：

- 在 index size 维度上，Pareto frontier 全部由 IVF+OPQ+PQ 构成；
- M8、M16、M24 形成了随 index size 增长、质量逐步提升的 frontier；
- M24 + IVF+OPQ+PQ 是当前最高质量点；
- M8 + IVF+OPQ+PQ 是当前最低 index size frontier 点。

---

### 5.2 Latency Pareto Frontier

生成文件：

```text
results/budgeted/joint_compression/day4_figures/day4_pareto_latency.csv
results/budgeted/joint_compression/day4_figures/day4_pareto_latency.md
```

Latency 维度上的 Pareto frontier 为：

| Run Name | N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| w6_N10_M8_ivf_opq_pq | 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.0553175 | 0.0990213 | 0.00616455 | 4.80393 |
| w6_N10_M8_none | 10 | 8 | None | 0.266667 | 0.0906878 | 0.1248650 | 1.57812 | 4.87238 |
| w6_N10_M24_pq | 10 | 24 | PQ | 0.266667 | 0.0889286 | 0.1254600 | 0.01849370 | 5.10507 |
| w6_N10_M24_ivf_opq_pq | 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.0956878 | 0.1295850 | 0.01849370 | 5.40662 |

观察：

- Latency frontier 包含低 latency 的 M8 + IVF+OPQ+PQ；
- M8 None 由于 latency 较低且 nDCG@10 较高，也进入 latency frontier；
- M24 PQ 是当前较好的 quality-latency trade-off 点；
- M24 IVF+OPQ+PQ 是最高质量点，但 latency 高于 M24 PQ；
- 在当前 reconstructed reranking 设置下，IVF 并未稳定带来 latency 下降，因此 latency frontier 的解释需要谨慎。

---

### 5.3 完整结果表与 Pareto Flags

生成文件：

```text
results/budgeted/joint_compression/day4_figures/day4_results_with_pareto_flags.csv
results/budgeted/joint_compression/day4_figures/day4_results_with_pareto_flags.md
```

该表在 Day 3 主结果基础上新增：

```text
pareto_index_size
pareto_latency
```

用于标记每个配置是否属于对应成本维度下的 Pareto frontier。

---

## 6. 今日标注的关键配置

根据 Day 3 代表点与 Day 4 图中标注，关键配置如下：

| Category | Run Name | N | M | Compression | Recall@10 | MRR@10 | nDCG@10 | Index Size MB | Latency ms/query |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| Closest to best quality | w6_N10_M24_ivf_opq_pq | 10 | 24 | IVF+OPQ+PQ | 0.266667 | 0.0956878 | 0.129585 | 0.0184937 | 5.40662 |
| Lowest cost | w6_N10_M8_ivf_opq_pq | 10 | 8 | IVF+OPQ+PQ | 0.266667 | 0.0553175 | 0.0990213 | 0.00616455 | 4.80393 |
| Best trade-off | w6_N10_M24_pq | 10 | 24 | PQ | 0.266667 | 0.0889286 | 0.125460 | 0.0184937 | 5.10507 |

---

## 7. 图注草稿

生成文件：

```text
results/budgeted/joint_compression/day4_figures/day4_figure_captions.md
```

### Figure 1: Quality vs. Index Size

This figure shows the relationship between retrieval quality, measured by nDCG@10, and estimated index size. Each point represents one joint budget configuration. Compressed configurations substantially reduce storage cost while preserving competitive retrieval quality.

### Figure 2: Quality vs. Retrieval Latency

This figure compares retrieval quality against per-query reranking latency. The plot highlights which compressed budget settings provide favorable speed-quality trade-offs under the current reconstructed-embedding reranking pipeline.

### Figure 3: Pareto Frontier

This figure marks configurations that are not dominated by another configuration with both lower cost and higher retrieval quality. Separate frontiers are shown for index size and latency.

---

## 8. 关键发现

### 8.1 Index Size Frontier 清晰支持压缩有效性

Index-size Pareto frontier 由三组 IVF+OPQ+PQ 构成：

```text
M8  + IVF+OPQ+PQ
M16 + IVF+OPQ+PQ
M24 + IVF+OPQ+PQ
```

这说明在当前实验设置下，随着 token budget 从 M8 增加到 M24，检索质量逐步提升，同时 index size 仍保持在极低范围内：

```text
0.00616455 MB → 0.01232910 MB → 0.01849370 MB
```

相比未压缩配置，这些点显著降低了存储成本。

---

### 8.2 M24 + IVF+OPQ+PQ 是当前最高质量点

最高质量配置为：

```text
w6_N10_M24_ivf_opq_pq
```

其结果为：

```text
Recall@10 = 0.266667
MRR@10    = 0.0956878
nDCG@10   = 0.129585
```

该点也是 index-size Pareto frontier 和 latency Pareto frontier 的共同成员。

---

### 8.3 M8 + IVF+OPQ+PQ 是最低成本 frontier 点

最低成本配置为：

```text
w6_N10_M8_ivf_opq_pq
```

其 index size 为：

```text
0.00616455 MB
```

该点在 index size 和 latency 两个维度上均属于 Pareto frontier，适合作为极致轻量 budgeted retrieval 配置。

---

### 8.4 M24 + PQ 是当前最佳 trade-off 点

Day 3 和 Day 4 均标记：

```text
w6_N10_M24_pq
```

为当前最佳 trade-off 点。

其指标为：

```text
Recall@10 = 0.266667
MRR@10    = 0.0889286
nDCG@10   = 0.125460
Index Size MB = 0.0184937
Latency ms/query = 5.10507
```

该配置质量接近最高质量点，同时 latency 低于 M24 + IVF+OPQ+PQ，并且实现了明显压缩。

---

### 8.5 Latency 结论需要谨慎解释

当前 latency 图反映的是 reconstructed embeddings 下的 late interaction reranking 时间，而不是完整 ANN 检索系统的真实 online latency。

因此：

- IVF 配置没有稳定表现出更低 latency；
- latency 差异更多来自当前 Python reranking pipeline；
- 论文中应将该指标表述为 `reranking latency under reconstructed-embedding evaluation`；
- 后续如实现真实 FAISS ANN 查询，应重新测量 end-to-end latency。

---

## 9. 今日发现的小问题

### 9.1 None 在部分输出表中显示为 nan

在 `day4_results_with_pareto_flags.md` 和 `day4_pareto_latency.md` 中，部分未压缩配置的 Compression 字段显示为：

```text
nan
```

对应实际配置为：

```text
None
```

这主要是 CSV 读取时 pandas 将字符串 `None` 识别为空值导致的显示问题，不影响数值结果和 Pareto 判断。

后续报告或最终表格中应统一修正为：

```text
None
```

---

### 9.2 图中文字存在轻微重叠

当前图中关键点集中在 M24 区域，导致部分标注存在轻微重叠，例如：

```text
Best quality
Best trade-off
M24
```

该问题不影响实验结论，但如果图要直接放入论文，后续可进一步微调：

- 调整 annotation offset；
- 减少每个点的 M 标签；
- 仅标注关键点；
- 分离 index-size frontier 和 latency frontier 为两张单独图；
- 使用更大的画布或 vector PDF 手动微调。

---

## 10. 今日完成文件清单

### 10.1 Core Figures

```text
results/budgeted/joint_compression/figures/quality_vs_index_size.pdf
results/budgeted/joint_compression/figures/quality_vs_index_size.png
results/budgeted/joint_compression/figures/quality_vs_latency.pdf
results/budgeted/joint_compression/figures/quality_vs_latency.png
results/budgeted/joint_compression/figures/pareto_frontier.pdf
results/budgeted/joint_compression/figures/pareto_frontier.png
```

### 10.2 Day 4 Figure Copies

```text
results/budgeted/joint_compression/day4_figures/quality_vs_index_size.pdf
results/budgeted/joint_compression/day4_figures/quality_vs_index_size.png
results/budgeted/joint_compression/day4_figures/quality_vs_latency.pdf
results/budgeted/joint_compression/day4_figures/quality_vs_latency.png
results/budgeted/joint_compression/day4_figures/pareto_frontier.pdf
results/budgeted/joint_compression/day4_figures/pareto_frontier.png
```

### 10.3 Pareto Tables

```text
results/budgeted/joint_compression/day4_figures/day4_pareto_index_size.csv
results/budgeted/joint_compression/day4_figures/day4_pareto_index_size.md
results/budgeted/joint_compression/day4_figures/day4_pareto_latency.csv
results/budgeted/joint_compression/day4_figures/day4_pareto_latency.md
```

### 10.4 Full Results with Pareto Flags

```text
results/budgeted/joint_compression/day4_figures/day4_results_with_pareto_flags.csv
results/budgeted/joint_compression/day4_figures/day4_results_with_pareto_flags.md
```

### 10.5 Figure Captions

```text
results/budgeted/joint_compression/day4_figures/day4_figure_captions.md
```

---

## 11. Day 4 验收状态

| Requirement | Status |
|---|---|
| Quality vs. Index Size 图已生成 | Completed |
| Quality vs. Retrieval Latency 图已生成 | Completed |
| Pareto Frontier 图已生成 | Completed |
| Index Size Pareto frontier 已识别 | Completed |
| Latency Pareto frontier 已识别 | Completed |
| 关键配置已标注 | Completed |
| 图注草稿已生成 | Completed |
| 可用于论文主实验章节的图文件已输出 | Completed |

---

## 12. 今日结论

Week 6 Day 4 已成功将 Day 3 的联合 budget 主结果转化为三张核心实验图，并完成了 Pareto frontier 分析。结果表明，在当前固定 N=10 的设置下，压缩配置能够显著降低 estimated index size，同时维持具有竞争力的 nDCG@10。

从 index-size 角度看，M8、M16、M24 三个 IVF+OPQ+PQ 配置构成了清晰的 Pareto frontier，其中 M24 + IVF+OPQ+PQ 达到最高 nDCG@10 = 0.129585，M8 + IVF+OPQ+PQ 则代表最低成本 frontier 点。与此同时，M24 + PQ 在质量和 latency 之间取得较好的平衡，可作为当前最佳 trade-off 配置。

Day 4 已完成论文主实验章节所需的三张核心图和对应图注草稿，可以进入 Day 5 的结果讨论、消融总结和论文文字整理阶段。
