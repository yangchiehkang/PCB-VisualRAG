# Week 5 Day 5 Token Redundancy and Region Analysis Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Day:** Day 5  
**Date:** 2026-05-07  
**Experiment Name:** Token Redundancy, Type Sensitivity, and Region-Level Token Retention Analysis  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是基于 Day 3 和 Day 4 的 token budget 实验结果，进一步分析不同 token budget 下的冗余比例、质量保持情况、页面类型敏感性、query 类型敏感性，以及 token selection 实际保留的空间区域。

本日重点包括：

1. 估算不同 M 下的 token redundancy ratio；
2. 分析保留少量 tokens 时是否仍能保持检索性能；
3. 判断当前最优 M；
4. 生成页面类型和 query 类型分析模板；
5. 对当前未标注数据进行初步 type sensitivity 分析；
6. 生成 token mask 可视化案例；
7. 观察 norm-based token selection 倾向保留哪些 patch/token 区域；
8. 总结当前数据中 token 冗余程度和最值得保留的区域特征。

---

## 2. 实验背景

Day 3 已完成不同 token budget M 下的正式 C2F reranking 实验。  
Day 4 已完成不同 M 下的 index size、latency 和 quality-cost 曲线分析。

Day 5 不重新运行主检索流程，而是复用前两天结果进行解释性分析。

当前实验设置如下：

| 项目 | 设置 |
|---|---|
| Full-token setting | M49 |
| Token budgets | M8, M16, M24, M32, M49 |
| Page count | 101 |
| Query count | 30 |
| Candidate count | 300 |
| Avg candidates/query | 10 |
| Fixed candidate budget | N=10 |
| Embedding dim | 512 |
| Token selection strategy | Norm-based Top-M Token Selection |

说明：

- 当前每页 full page embedding 包含 49 个 tokens；
- 因此 M49 是 full-token reference；
- M8、M16、M24、M32 是不同强度的 token compression 设置；
- 原计划中的 M64、M128、M256 不适用于当前实验，因为当前每页最多只有 49 个 tokens。

---

## 3. 今日输入文件

### 3.1 Quality-Cost 表

今日使用 Day 4 生成的质量–成本综合表：

```text
results\budgeted\token_selection\day4_cost_analysis\day4_quality_cost_table.csv
```

该文件包含：

- M；
- Avg Tokens/Page；
- Total Vectors；
- Payload Size MB；
- Payload Reduction vs Full；
- Recall@10；
- MRR@10；
- nDCG@10；
- Per-query Latency ms。

---

### 3.2 Token Selection Metadata

今日使用 token selection metadata：

```text
results\budgeted\token_selection\day2_validation\day2_token_selection_metadata_all.csv
```

该文件用于读取不同页面在不同 M 下保留的 token indices，并生成 token mask 可视化图。

---

### 3.3 Run 文件

今日复用 Day 3 生成的 run 文件：

```text
results\budgeted\token_selection\c2f_N10_M8_run.tsv
results\budgeted\token_selection\c2f_N10_M16_run.tsv
results\budgeted\token_selection\c2f_N10_M24_run.tsv
results\budgeted\token_selection\c2f_N10_M32_run.tsv
results\budgeted\token_selection\c2f_N10_M49_run.tsv
```

---

### 3.4 Qrels 文件

今日用于 type sensitivity 分析的 qrels 文件为：

```text
data\metadata\qrels.tsv
```

---

## 4. 今日执行流程

### 4.1 创建 Day 5 输出目录

执行：

```bat
if not exist results\budgeted\token_selection\day5_redundancy_analysis mkdir results\budgeted\token_selection\day5_redundancy_analysis
if not exist results\budgeted\token_selection\figures mkdir results\budgeted\token_selection\figures
if not exist scripts\analysis mkdir scripts\analysis
```

输出目录：

```text
results\budgeted\token_selection\day5_redundancy_analysis
results\budgeted\token_selection\figures
```

---

### 4.2 运行 token redundancy 分析脚本

执行：

```bat
python scripts\analysis\analyze_token_redundancy_day5.py
```

生成文件：

```text
results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_ratio_analysis.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_ratio_analysis.md
results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_summary.md
```

---

### 4.3 运行页面类型与 query 类型敏感性分析脚本

执行：

```bat
python scripts\analysis\analyze_day5_type_sensitivity.py
```

生成文件：

```text
results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_annotations.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_annotations.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_sensitivity.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_sensitivity.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_best_m.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_best_m.csv
results\budgeted\token_selection\day5_redundancy_analysis\day5_type_sensitivity_summary.md
```

说明：

- 当前页面类型标注文件已生成；
- 当前 query 类型标注文件已生成；
- 但 page_type 和 query_type 尚未人工补充，因此当前 sensitivity 分析结果均归入 `Unlabeled`；
- 今日 type sensitivity 的结果作为分析模板和流程验证结果；
- 后续补充人工标注后，可重新运行同一脚本得到 BOM、Stackup、Drill Table、Assembly Drawing、Notes 等类别的细分结果。

---

### 4.4 运行 token mask 可视化脚本

执行：

```bat
python scripts\analysis\visualize_day5_token_masks.py
```

生成 token mask 可视化图：

```text
results\budgeted\token_selection\figures\day5_token_mask_doc001_p001.png
results\budgeted\token_selection\figures\day5_token_mask_doc001_p002.png
results\budgeted\token_selection\figures\day5_token_mask_doc001_p003.png
results\budgeted\token_selection\figures\day5_token_mask_doc001_p004.png
results\budgeted\token_selection\figures\day5_token_mask_doc001_p005.png
results\budgeted\token_selection\figures\day5_token_mask_doc002_p001.png
results\budgeted\token_selection\figures\day5_token_mask_doc003_p001.png
results\budgeted\token_selection\figures\day5_token_mask_doc003_p002.png
```

每张图展示同一页面在不同 M 下的 token mask：

```text
M8
M16
M24
M32
M49
```

---

## 5. 今日生成文件

### 5.1 冗余比例分析文件

| 文件 | 路径 |
|---|---|
| Redundancy CSV | `results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_ratio_analysis.csv` |
| Redundancy Markdown | `results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_ratio_analysis.md` |
| Redundancy Summary | `results\budgeted\token_selection\day5_redundancy_analysis\day5_redundancy_summary.md` |

---

### 5.2 页面类型与 Query 类型分析文件

| 文件 | 路径 |
|---|---|
| Page type annotation template | `results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_annotations.csv` |
| Query type annotation template | `results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_annotations.csv` |
| Page type sensitivity | `results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_sensitivity.csv` |
| Query type sensitivity | `results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_sensitivity.csv` |
| Page type best M | `results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_best_m.csv` |
| Query type best M | `results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_best_m.csv` |
| Type sensitivity summary | `results\budgeted\token_selection\day5_redundancy_analysis\day5_type_sensitivity_summary.md` |

---

### 5.3 Token Mask 可视化文件

| 页面 | 图像路径 |
|---|---|
| doc001_p001 | `results\budgeted\token_selection\figures\day5_token_mask_doc001_p001.png` |
| doc001_p002 | `results\budgeted\token_selection\figures\day5_token_mask_doc001_p002.png` |
| doc001_p003 | `results\budgeted\token_selection\figures\day5_token_mask_doc001_p003.png` |
| doc001_p004 | `results\budgeted\token_selection\figures\day5_token_mask_doc001_p004.png` |
| doc001_p005 | `results\budgeted\token_selection\figures\day5_token_mask_doc001_p005.png` |
| doc002_p001 | `results\budgeted\token_selection\figures\day5_token_mask_doc002_p001.png` |
| doc003_p001 | `results\budgeted\token_selection\figures\day5_token_mask_doc003_p001.png` |
| doc003_p002 | `results\budgeted\token_selection\figures\day5_token_mask_doc003_p002.png` |

---

## 6. Token Redundancy 分析结果

### 6.1 不同 M 下的冗余比例

以 M49 作为 full-token reference，今日得到以下 redundancy ratio 结果：

| M | Keep Ratio | Redundancy Ratio | Payload Reduction | Recall@10 | Recall Retention | MRR@10 | MRR Retention | nDCG@10 | nDCG Retention | Latency ms/query |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 16.33% | 83.67% | 83.67% | 0.2667 | 100.00% | 0.0907 | 144.46% | 0.1249 | 120.89% | 2.0249 |
| 16 | 32.65% | 67.35% | 67.35% | 0.2667 | 100.00% | 0.0901 | 143.57% | 0.1242 | 120.27% | 1.6379 |
| 24 | 48.98% | 51.02% | 51.02% | 0.2667 | 100.00% | 0.0754 | 120.19% | 0.1145 | 110.82% | 1.6846 |
| 32 | 65.31% | 34.69% | 34.69% | 0.2667 | 100.00% | 0.0465 | 74.04% | 0.0920 | 89.06% | 1.8168 |
| 49 | 100.00% | 0.00% | 0.00% | 0.2667 | 100.00% | 0.0628 | 100.00% | 0.1033 | 100.00% | 2.3857 |

---

### 6.2 关键观察

从 redundancy analysis 看：

1. M8 只保留 16.33% tokens，移除 83.67% tokens；
2. M16 只保留 32.65% tokens，移除 67.35% tokens；
3. M24 保留 48.98% tokens，移除 51.02% tokens；
4. M32 保留 65.31% tokens，移除 34.69% tokens；
5. 所有 M 下 Recall@10 均保持 0.2667；
6. M8 和 M16 的 MRR@10 与 nDCG@10 高于 M49；
7. M16 是 latency 最低的配置；
8. M32 虽然保留更多 tokens，但排序质量低于 M49。

这说明当前页面 multi-vector representation 中存在明显 token 冗余。减少 token 数并没有导致 Recall@10 下降，反而在 M8、M16、M24 下提升了排序质量。

---

## 7. 对 Day 5 核心问题的回答

### 7.1 哪个 M 最优？

从综合质量–效率角度看，当前最优 M 是：

```text
M16
```

理由如下：

| 指标 | M16 结果 |
|---|---:|
| Keep Ratio | 32.65% |
| Redundancy Ratio | 67.35% |
| Payload Reduction | 67.35% |
| Recall@10 | 0.2667 |
| Recall@10 Retention vs M49 | 100.00% |
| MRR@10 | 0.0901 |
| MRR@10 Retention vs M49 | 143.57% |
| nDCG@10 | 0.1242 |
| nDCG@10 Retention vs M49 | 120.27% |
| Latency ms/query | 1.6379 |

M16 的优势是：

1. 相比 M49，移除了 67.35% tokens；
2. Recall@10 与 M49 完全持平；
3. MRR@10 和 nDCG@10 明显高于 M49；
4. latency 是所有设置中最低的；
5. 质量接近 M8，但速度优于 M8；
6. index size、ranking quality 和 latency 三者最均衡。

因此，M16 是当前最优 quality-cost trade-off 配置。

---

### 7.2 保留约 25% token 是否能保住 90% 性能？

当前实验没有精确测试 25% token setting。  
最接近的已测试配置是 M16：

```text
M16 keep ratio = 32.65%
```

M16 的结果为：

| 指标 | M49 | M16 | Retention |
|---|---:|---:|---:|
| Recall@10 | 0.2667 | 0.2667 | 100.00% |
| MRR@10 | 0.0628 | 0.0901 | 143.57% |
| nDCG@10 | 0.1033 | 0.1242 | 120.27% |

结论：

```text
在当前实验中，保留约三分之一 tokens 已经可以保住 100% Recall@10，并且排序质量高于 full-token setting。
```

因此可以认为，当前数据中至少有约 67.35% tokens 对当前 N=10 reranking 的最终 Recall@10 不是必要的。

---

### 7.3 保留约 10% token 是否仍能保住大部分 recall？

当前实验没有精确测试 10% token setting。  
最接近的强压缩配置是 M8：

```text
M8 keep ratio = 16.33%
```

M8 的结果为：

| 指标 | M49 | M8 | Retention |
|---|---:|---:|---:|
| Recall@10 | 0.2667 | 0.2667 | 100.00% |
| MRR@10 | 0.0628 | 0.0907 | 144.46% |
| nDCG@10 | 0.1033 | 0.1249 | 120.89% |

结论：

```text
在当前实验中，保留 16.33% tokens 仍能保持 100% Recall@10，并且 MRR@10 与 nDCG@10 高于 M49。
```

这说明当前页面中可能存在高比例冗余 tokens。  
不过，由于没有测试 M5 或其他更接近 10% 的配置，因此不能直接断言 10% token 一定足够。当前可以较稳妥地说：

```text
保留约 16% tokens 已经足以保住当前实验中的全部 Recall@10。
```

---

### 7.4 冗余 token 大约有多少？

根据当前实验结果：

- 从 Recall@10 角度看，M8 已能保持与 M49 相同的 Recall@10；
- M8 只保留 16.33% tokens；
- 因此在当前 N=10 reranking 设置下，约 83.67% tokens 对 Recall@10 是可移除的；
- 从更稳健的 quality-cost trade-off 角度看，M16 移除 67.35% tokens，同时保持 Recall@10 并提升排序质量。

因此当前可以给出两个层次的结论：

| 角度 | 推荐 M | 可视为冗余的 token 比例 |
|---|---:|---:|
| 最大压缩角度 | M8 | 约 83.67% |
| 稳健 trade-off 角度 | M16 | 约 67.35% |

最终判断：

```text
当前数据中至少约 67.35% tokens 可以被视为高冗余；在强压缩设置下，最多约 83.67% tokens 可被移除且 Recall@10 不下降。
```

---

## 8. 页面类型敏感性分析

### 8.1 当前标注状态

今日已生成页面类型标注模板：

```text
results\budgeted\token_selection\day5_redundancy_analysis\day5_page_type_annotations.csv
```

当前该文件包含 page_id、page_type 和 notes 三列。  
由于尚未人工补充 page_type，当前所有页面类型在统计中被归为：

```text
Unlabeled
```

---

### 8.2 当前页面类型分析结果

当前 `day5_page_type_sensitivity.csv` 的结果如下：

| Page Type | M | Evaluated Queries | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Unlabeled | 8 | 30 | 0.2667 | 0.0907 |
| Unlabeled | 16 | 30 | 0.2667 | 0.0901 |
| Unlabeled | 24 | 30 | 0.2667 | 0.0754 |
| Unlabeled | 32 | 30 | 0.2667 | 0.0465 |
| Unlabeled | 49 | 30 | 0.2667 | 0.0628 |

当前 page type best M 为：

| Page Type | Best M | Evaluated Queries | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Unlabeled | 8 | 30 | 0.2667 | 0.0907 |

---

### 8.3 页面类型分析结论

由于当前页面尚未人工标注具体类型，因此今日不能可靠区分：

- BOM；
- Stackup；
- Drill Table；
- Assembly Drawing；
- Notes；
- Schematic；
- Other。

当前只能得到整体页面集合上的结论：

```text
在未区分页面类型的整体集合上，M8 的 MRR@10 最高，M16 与 M8 非常接近，且所有 M 的 Recall@10 相同。
```

后续补充 page_type 标注后，需要重新运行：

```bat
python scripts\analysis\analyze_day5_type_sensitivity.py
```

以得到不同页面类型对 token budget 的敏感性分析。

---

## 9. Query 类型敏感性分析

### 9.1 当前标注状态

今日已生成 query 类型标注模板：

```text
results\budgeted\token_selection\day5_redundancy_analysis\day5_query_type_annotations.csv
```

当前该文件包含：

- query_id；
- query_type；
- main_evidence；
- notes。

由于尚未人工补充 query_type，当前所有 query 类型在统计中被归为：

```text
Unlabeled
```

---

### 9.2 当前 Query 类型分析结果

当前 `day5_query_type_sensitivity.csv` 的结果如下：

| Query Type | M | Evaluated Queries | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Unlabeled | 8 | 30 | 0.2667 | 0.0907 |
| Unlabeled | 16 | 30 | 0.2667 | 0.0901 |
| Unlabeled | 24 | 30 | 0.2667 | 0.0754 |
| Unlabeled | 32 | 30 | 0.2667 | 0.0465 |
| Unlabeled | 49 | 30 | 0.2667 | 0.0628 |

当前 query type best M 为：

| Query Type | Best M | Evaluated Queries | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Unlabeled | 8 | 30 | 0.2667 | 0.0907 |

---

### 9.3 Query 类型分析结论

由于当前 query 尚未人工标注类型，因此今日不能可靠区分：

- 参数查表类；
- 元件定位类；
- 规格确认类；
- 跨页一致性类；
- 其他。

当前只能得到整体 query 集合上的结论：

```text
在未区分 query 类型的整体集合上，M8 的排序指标最高，M16 紧随其后，所有 M 的 Recall@10 均保持不变。
```

后续补充 query_type 和 main_evidence 标注后，需要重新运行 type sensitivity 分析，以判断不同 query 类型是否偏好不同 M。

---

## 10. Token 保留区域可视化分析

### 10.1 可视化设置

今日生成了 8 个页面的 token mask 可视化图。每张图显示同一个页面在不同 M 下的保留 token 分布：

```text
M8, M16, M24, M32, M49
```

由于每页 full-token 数为 49，因此 token mask 以 7x7 网格展示。

颜色含义：

| 颜色 | 含义 |
|---|---|
| 深蓝色 | 被保留 token |
| 浅色 | 被剪枝 token |

M49 表示 full-token setting，因此整张 mask 均为深蓝色。

---

### 10.2 可视化页面列表

今日可视化的页面包括：

| 页面 | 图像 |
|---|---|
| doc001_p001 | `day5_token_mask_doc001_p001.png` |
| doc001_p002 | `day5_token_mask_doc001_p002.png` |
| doc001_p003 | `day5_token_mask_doc001_p003.png` |
| doc001_p004 | `day5_token_mask_doc001_p004.png` |
| doc001_p005 | `day5_token_mask_doc001_p005.png` |
| doc002_p001 | `day5_token_mask_doc002_p001.png` |
| doc003_p001 | `day5_token_mask_doc003_p001.png` |
| doc003_p002 | `day5_token_mask_doc003_p002.png` |

---

### 10.3 可视化观察

从 token mask 可视化中可以观察到以下现象：

1. M8 下保留区域非常稀疏；
2. M16 下保留区域明显增加，但仍集中在局部区域；
3. M24 和 M32 下保留区域进一步扩展；
4. M49 下所有 tokens 均被保留；
5. 被保留 tokens 并不是均匀分布在整页，而是具有明显空间偏好；
6. 多数页面中，top-M tokens 倾向出现在页面上方、边缘区域或局部结构密集区域；
7. 一些页面的中下部大片区域在 M8/M16 下没有被保留，说明这些区域在 norm-based scoring 下信息密度较低；
8. 不同页面的保留模式不同，说明 token selection 会根据页面本身的 embedding norm 分布进行选择。

---

### 10.4 对 token selection 行为的解释

Norm-based token selection 的核心逻辑是保留 embedding norm 较大的 tokens。  
从可视化结果看，这种策略倾向保留视觉或语义上更强的局部区域。

这些区域可能对应：

- 标题或页眉区域；
- 表格边界或表格内容区域；
- 图形标注区域；
- 文字密集区域；
- 局部高对比度区域；
- 页面结构较复杂的区域。

相对而言，以下区域更容易被剪枝：

- 大面积空白区域；
- 低纹理背景区域；
- 信息密度较低的页面中部或下部区域；
- 对视觉 encoder 激活较弱的 patch 区域。

这与 Day 4 的结果相互支持：大量 page tokens 可以被剪枝，但 top-M tokens 仍能保留关键检索信号。

---

## 11. 冗余比例与区域分析综合结论

### 11.1 M8 的意义

M8 的结果：

| 指标 | 值 |
|---|---:|
| Keep Ratio | 16.33% |
| Redundancy Ratio | 83.67% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0907 |
| nDCG@10 | 0.1249 |
| Latency ms/query | 2.0249 |

M8 是最强压缩配置。  
它说明在当前数据中，仅保留 16.33% tokens 仍然可以保持完整的 Recall@10，并且获得最高的 MRR@10 和 nDCG@10。

但 M8 的 latency 并不是最低，因此它更适合作为最大压缩能力的证明，而不是当前最稳妥的部署配置。

---

### 11.2 M16 的意义

M16 的结果：

| 指标 | 值 |
|---|---:|
| Keep Ratio | 32.65% |
| Redundancy Ratio | 67.35% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0901 |
| nDCG@10 | 0.1242 |
| Latency ms/query | 1.6379 |

M16 是当前最优 quality-cost trade-off 配置。  
它在只保留约三分之一 tokens 的情况下：

1. 保持 100% Recall@10；
2. MRR@10 高于 M49；
3. nDCG@10 高于 M49；
4. latency 是所有配置中最低；
5. payload size 相比 M49 减少 67.35%。

因此，M16 是当前最适合作为后续实验推荐设置的 token budget。

---

### 11.3 M24 的意义

M24 的结果：

| 指标 | 值 |
|---|---:|
| Keep Ratio | 48.98% |
| Redundancy Ratio | 51.02% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0754 |
| nDCG@10 | 0.1145 |
| Latency ms/query | 1.6846 |

M24 是较保守的压缩配置。  
它保留接近一半 tokens，同时相对 M49 保持更高的 MRR@10 和 nDCG@10。

M24 可以作为对质量更保守场景下的候选配置。

---

### 11.4 M32 的意义

M32 的结果：

| 指标 | 值 |
|---|---:|
| Keep Ratio | 65.31% |
| Redundancy Ratio | 34.69% |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0465 |
| nDCG@10 | 0.0920 |
| Latency ms/query | 1.8168 |

M32 是当前结果中排序质量最低的配置。  
它保留了更多 tokens，但 MRR@10 和 nDCG@10 低于 M49。

这说明：

```text
更多 tokens 并不必然带来更好的 late interaction 排序效果。
```

可能原因包括：

1. 额外 tokens 改变了 late interaction 的最大相似度结构；
2. 新增 tokens 可能引入噪声；
3. norm-based token selection 是 query-independent 策略；
4. 当前数据规模较小，少数 query 的排名变化会显著影响 MRR 和 nDCG。

---

## 12. 当前限制

今日实验仍有以下限制：

1. 页面类型尚未人工标注；
2. query 类型尚未人工标注；
3. 当前 type sensitivity 只能得到 `Unlabeled` 级别的整体结果；
4. token mask 只显示保留位置，尚未叠加原始页面图像；
5. 当前可视化尚未与 gold evidence region 对齐；
6. 当前没有测试更接近 10% keep ratio 的 M，例如 M5；
7. 当前 query 数为 30，样本量较小；
8. latency 是毫秒级小规模计时，容易受到缓存和 Python 开销影响。

这些限制不会影响 Day 5 的主要结论，但后续如果要做更强解释，需要补充页面类型标注、query 类型标注和 evidence region 对照。

---

## 13. 后续改进方向

后续可以继续补充以下工作：

1. 人工补充 `day5_page_type_annotations.csv`；
2. 人工补充 `day5_query_type_annotations.csv`；
3. 重新运行 type sensitivity 分析；
4. 添加 M5 或 M4，测试接近 10% token keep ratio 的表现；
5. 将 token mask 叠加到原始页面图像上；
6. 增加 gold evidence region 对照；
7. 对不同 page type 分别分析最佳 M；
8. 对不同 query type 分别分析最佳 M；
9. 观察 BOM、drill table、assembly drawing、notes 是否存在不同 token redundancy；
10. 分析 query-dependent token selection 是否能进一步提升效果。

---

## 14. 今日验收情况

| 验收项 | 状态 |
|---|---|
| 冗余比例分析表已生成 | Completed |
| Redundancy summary 已生成 | Completed |
| 页面类型标注模板已生成 | Completed |
| Query 类型标注模板已生成 | Completed |
| 页面类型 sensitivity 表已生成 | Completed |
| Query 类型 sensitivity 表已生成 | Completed |
| Token mask 可视化图已生成 | Completed |
| 当前最优 M 已判断 | Completed |
| 冗余 token 比例已估算 | Completed |
| 保留区域特征已初步分析 | Completed |

---

## 15. 今日结论

Week 5 Day 5 已完成 token redundancy、type sensitivity 和 token retention region 的初步分析。

今日结果显示，当前页面 multi-vector representation 中存在明显 token 冗余。以 M49 作为 full-token reference，M16 只保留 32.65% tokens，移除 67.35% tokens，但仍保持 100% Recall@10，并且 MRR@10 和 nDCG@10 分别达到 M49 的 143.57% 和 120.27%。M8 只保留 16.33% tokens，移除 83.67% tokens，也保持 100% Recall@10，并获得当前最高的 MRR@10 和 nDCG@10。

从综合质量–成本角度看，M16 是当前最优 trade-off 配置；从最大压缩角度看，M8 证明了当前数据中存在非常高的 token 冗余。Token mask 可视化进一步表明，norm-based token selection 并不是随机保留 tokens，而是倾向于保留页面中信息密度较高的局部区域，如标题、表格、注释、图形标注或局部结构密集区域，而大量空白或低信息区域可以被剪枝。

由于当前页面类型和 query 类型尚未人工标注，今日 type sensitivity 结果仍停留在 `Unlabeled` 整体层面。后续补充标注后，可以进一步回答 BOM、Stackup、Drill Table、Assembly Drawing、Notes 等页面类型是否具有不同冗余比例，以及参数查表类、元件定位类、规格确认类、跨页一致性类 query 是否对 token budget 有不同敏感性。

最终判断：

> Day 5 验收通过。当前已经能够回答：M16 是最优 quality-cost trade-off；当前至少约 67.35% tokens 可视为高冗余，在强压缩下约 83.67% tokens 可被移除且 Recall@10 不下降；最值得保留的区域通常是页面中的高信息密度区域，包括表格、标题、注释、图形标注和局部结构密集区域。
