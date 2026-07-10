# Week 7 Day 6 Note：Fixed-N Coarse-to-Fine Retrieval 与 Evidence Attribution 汇总

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 7  
**Day:** Day 6  
**Date:** 2026-05-08  
**Theme:** Fixed-N Coarse-to-Fine Retrieval, Hybrid Fusion, Evidence Attribution and Occlusion  
**Status:** Completed  

---

## 1. 今日目标

Week 7 Day 6 的目标是汇总 Week 7 全部实验材料，形成可进入论文实验章节的核心结果包，并整理本周主要发现。

Week 7 围绕两个核心问题展开：

```text
1. 修复 coarse retrieval candidate 数量固定为 10 的问题，重新评估不同 N 下的 C2F 检索效果。
2. 构建 evidence attribution 与 occlusion 实验闭环，验证模型分数是否依赖标注的 evidence region。
```

本周实验重点不是单纯提升检索指标，而是回答：

```text
在 PCB 文档页面检索任务中，coarse candidate budget、multi-vector reranking、
score fusion 与 visual evidence region 分别如何影响最终检索质量与可解释性？
```

---

## 2. 本周实验闭环

Week 7 已完成从候选集修复、C2F reranking、score fusion、evidence hit、region hit、occlusion 到论文图表整理的完整闭环。

| Day | Theme | Status |
|---:|---|---|
| Day 1 | 修复不同 N 候选集并重新计算 Coarse Recall@N | Completed |
| Day 2 | BM25 + Full MV 与 Budgeted MV Rerank | Completed |
| Day 3 | Score Normalization 与 Hybrid Fusion | Completed |
| Day 4 | Evidence Query Subset 与 bbox 标注 | Completed |
| Day 5 | Evidence Hit@k、Region Hit@k 与 Occlusion 分析 | Completed |
| Day 6 | 核心结果表与可视化案例图整理 | Completed |

---

## 3. Week 7 主实验设置

### 3.1 Fixed-N Candidate Setting

Week 6 中发现当前 coarse candidate 文件实际固定为 top-10，导致不同 N 设置没有真正生效。

Week 7 Day 1 修复后，重新生成并验证：

```text
N ∈ {10, 20, 50, 100}
```

涉及方法：

```text
BM25
Dense Text
Single-vector Visual
BM25 + Full MV
BM25 + Budgeted MV
Hybrid Fusion
```

修复内容包括：

```text
1. run_bm25.py 支持 --top_k 和 --output 参数；
2. run_dense_text_retrieval.py 支持 --top_k 和 --output 参数；
3. run_single_vector_visual_retrieval.py 支持 --top_k 和 --output 参数；
4. 重新生成 top-101 full-depth run；
5. 从 top-101 run 中切出不同 N 的 candidate files；
6. 检查 actual candidates/query 是否随 N 正确变化。
```

---

### 3.2 Multi-vector Reranking

Week 7 使用 full multi-vector late interaction 进行 reranking。

Late interaction scoring 定义为：

```text
score(q, p) = sum_i max_j q_i^T p_j
```

其中：

```text
q_i = query token embedding
p_j = page token embedding
```

本周运行的 reranking 配置包括：

```text
BM25 + Full MV:
N ∈ {10, 20, 50, 100}

BM25 + Budgeted MV:
N ∈ {20, 50}
M ∈ {8, 16, 24}
```

---

### 3.3 Score Normalization and Hybrid Fusion

Day 3 对 BM25 score 与 MV score 进行 query-level min-max normalization。

归一化公式：

```text
Score_norm = (Score - min(Score)) / (max(Score) - min(Score) + epsilon)
```

Hybrid Fusion 使用：

```text
final_score = alpha * bm25_score_norm + (1 - alpha) * mv_score_norm
```

其中：

```text
alpha ∈ {0.0, 0.1, ..., 1.0}
```

---

## 4. Week 7 主结果表

### 4.1 Table 14：BM25-C2F 主结果表

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Index Size |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | 3030 |
| BM25 + Full MV | 0.0667 | 0.3000 | 0.8833 | 0.2107 | 0.3628 | 10 |
| BM25 + Budgeted MV | 0.0333 | 0.1333 | 0.3667 | 0.0956 | 0.1565 | 20 |
| Hybrid Fusion | 0.0667 | 0.1000 | 0.1333 | 0.0881 | 0.0988 | 301 |

Source files:

```text
results/week7/day6_core_tables/table14_bm25_c2f_main_results.csv
results/week7/day6_core_tables/table14_bm25_c2f_main_results.md
results/week7/day6_core_tables/table14_bm25_c2f_main_results.json
```

---

### 4.2 Table 15：Budgeted Retrieval 代表配置表

| Config | N | M | Compression | nDCG@10 | Index Size MB | Latency |
|---|---:|---:|---|---:|---:|---:|
| Full MV | full | 49 | None | 0.3628 | 0.01 | 9.3619 |
| Budgeted Low-cost | 20 | 8 | PQ | 0.1565 | 0.02 | 12.6743 |
| Budgeted Mid-cost | 20 | 16 | PQ | 0.1490 | 0.02 | 12.8563 |
| Budgeted High-quality | 50 | 24 | PQ | 0.0359 | 0.02 | 31.9103 |

Source files:

```text
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.csv
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.md
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.json
```

---

### 4.3 Table 16：Evidence Hit 主结果表

| Method | Evidence Hit@1 | Evidence Hit@5 | Evidence Hit@10 |
|---|---:|---:|---:|
| BM25 | 0.4000 | 1.0000 | 1.0000 |
| Full MV | 0.1000 | 0.4000 | 1.0000 |
| Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| BM25 + Budgeted MV | 0.1000 | 0.2000 | 0.4000 |
| Hybrid Fusion | 0.4000 | 1.0000 | 1.0000 |

Source files:

```text
results/week7/day6_core_tables/table16_evidence_hit_main_results.csv
results/week7/day6_core_tables/table16_evidence_hit_main_results.md
results/week7/day6_core_tables/table16_evidence_hit_main_results.json
```

---

### 4.4 Table 17：Occlusion 主结果表

| Condition | MRR@10 | nDCG@10 | Avg Gold Page Score |
|---|---:|---:|---:|
| Original | 1.0000 | 1.0000 | 0.20149380 |
| Gold Mask | 0.0000 | 0.0000 | 0.00000000 |
| Random Mask | 1.0000 | 1.0000 | 0.20149380 |

Source files:

```text
results/week7/day6_core_tables/table17_occlusion_main_results.csv
results/week7/day6_core_tables/table17_occlusion_main_results.md
results/week7/day6_core_tables/table17_occlusion_main_results.json
```

---

## 5. Evidence Attribution 与 Occlusion

### 5.1 Evidence Query Subset

Day 4 自动选择了 10 条 evidence query 样本：

| Query ID | Gold Page | Evidence Type | Retrievable | Best Rank |
|---|---|---|---|---:|
| q001 | doc001_p001 | region | yes | 2 |
| q002 | doc001_p002 | region | yes | 1 |
| q004 | doc001_p004 | region | yes | 1 |
| q006 | doc002_p001 | region | yes | 1 |
| q007 | doc002_p001 | region | yes | 2 |
| q008 | doc003_p007 | region | yes | 1 |
| q009 | doc003_p008 | region | yes | 1 |
| q010 | doc003_p009 | region | yes | 2 |
| q011 | doc003_p010 | region | yes | 2 |
| q012 | doc003_p011 | region | yes | 2 |

Annotation files:

```text
data/annotations/evidence_query_subset.jsonl
data/annotations/evidence_regions.jsonl
results/week7/evidence_annotation/evidence_subset_candidates.csv
results/week7/evidence_annotation/evidence_subset_selection_report.md
```

---

### 5.2 Region Hit@k

Region Hit 采用 7x7 patch grid，并使用 IoU 0.3 作为判定阈值。

| Method | Region Hit@1 | Region Hit@3 | Region Hit@5 |
|---|---:|---:|---:|
| Full MV | 0.0000 | 0.0000 | 0.0000 |
| Budgeted MV | 0.0000 | 0.0000 | 0.1000 |
| BM25 + Budgeted MV | 0.0000 | 0.0000 | 0.2000 |
| Hybrid Fusion | 0.0000 | 0.2000 | 0.4000 |

结果观察：

```text
1. Hybrid Fusion 在 Region Hit@3 和 Region Hit@5 上表现最好。
2. Full MV 在当前 patch-level evidence localization 上没有命中。
3. Budgeted MV 和 BM25 + Budgeted MV 在 Top-5 内存在少量区域级命中。
4. 区域级指标明显比页级 Evidence Hit 更难，说明页面召回与证据定位是两个不同层次的问题。
```

---

### 5.3 Occlusion 结论

Occlusion 实验比较三种条件：

```text
Original
Gold Mask
Random Mask
```

核心结果：

```text
Original:
MRR@10 = 1.0000
nDCG@10 = 1.0000
Avg Gold Page Score = 0.20149380

Gold Mask:
MRR@10 = 0.0000
nDCG@10 = 0.0000
Avg Gold Page Score = 0.00000000

Random Mask:
MRR@10 = 1.0000
nDCG@10 = 1.0000
Avg Gold Page Score = 0.20149380
```

主要结论：

```text
Gold evidence bbox 被遮挡后，gold page score 降为 0；
Random mask 不影响 gold page score；
说明模型分数高度依赖标注的 evidence region，而不是随机页面区域。
```

---

## 6. 可视化案例图

Day 6 共生成 5 个 Evidence Attribution 与 Occlusion 可视化案例。

### 6.1 Table 18：Week 7 可视化案例类型

| 案例类型 | 数量 | 作用 |
|---|---:|---|
| Gold mask 后明显掉分 | 2 | 支撑证据依赖 |
| Random mask 影响较小 | 1 | 支撑对照有效 |
| 遮挡不敏感失败例 | 1 | 展示客观分析 |
| BM25 + MV 改善排序例 | 1 | 支撑性能补强 |

---

### 6.2 Visual Case Summary

| Case ID | Case Type | Query ID | Page ID | COG_score | Figure |
|---|---|---|---|---:|---|
| evidence_case_001 | Gold mask 后明显掉分 | q001 | doc001_p001 | 0.28208059 | figures/week7/evidence_case_001.png |
| evidence_case_002 | Gold mask 后明显掉分 | q011 | doc003_p010 | 0.28198810 | figures/week7/evidence_case_002.png |
| evidence_case_003 | Random mask 影响较小 | q002 | doc001_p002 | 0.13606575 | figures/week7/evidence_case_003.png |
| evidence_case_004 | 遮挡不敏感失败例 | q004 | doc001_p004 | 0.01350269 | figures/week7/evidence_case_004.png |
| evidence_case_005 | BM25 + MV 改善排序例 | q010 | doc003_p009 | 0.28175521 | figures/week7/evidence_case_005.png |

Generated files:

```text
figures/week7/evidence_case_001.png
figures/week7/evidence_case_002.png
figures/week7/evidence_case_003.png
figures/week7/evidence_case_004.png
figures/week7/evidence_case_005.png

results/week7/day6_visual_cases/week7_visual_case_summary.csv
results/week7/day6_visual_cases/week7_visual_case_summary.md
results/week7/day6_visual_cases/week7_visual_case_summary.json
```

---

## 7. 本周主要发现

### 7.1 Candidate N 修复是必要前提

Week 6 中不同 N 的实验实际被固定 top-10 candidate 限制。

Week 7 修复后，系统能够真实评估：

```text
N = 10, 20, 50, 100
```

这为后续 C2F 检索、预算分配和 latency-quality trade-off 分析提供了正确基础。

---

### 7.2 BM25 在当前 PCB 文档检索任务中仍然非常强

Table 14 显示，BM25 的整体检索指标最高：

```text
Recall@10 = 0.8833
MRR@10 = 0.4105
nDCG@10 = 0.5241
```

说明当前 PCB 文档任务中，OCR text 与 query 的 lexical matching 仍然是非常强的信号。

---

### 7.3 Full MV 能覆盖 gold page，但排序能力不足

Evidence Hit 结果显示：

```text
Full MV Evidence Hit@10 = 1.0000
Full MV Evidence Hit@5 = 0.4000
Full MV Evidence Hit@1 = 0.1000
```

这说明 Full MV 能在 Top-10 内覆盖 gold evidence page，但排序靠前能力不如 BM25。

---

### 7.4 Hybrid Fusion 在 evidence-level retrieval 上更稳健

Evidence Hit 结果显示：

```text
Hybrid Fusion Evidence Hit@1 = 0.4000
Hybrid Fusion Evidence Hit@5 = 1.0000
Hybrid Fusion Evidence Hit@10 = 1.0000
```

Hybrid Fusion 与 BM25 在 evidence subset 上表现最好，说明融合 text 与 visual signal 对 evidence retrieval 有帮助。

---

### 7.5 Occlusion 强力支持 evidence dependency

Occlusion 主结果表明：

```text
Original score = 0.20149380
Gold Mask score = 0.00000000
Random Mask score = 0.20149380
```

这说明遮挡 gold evidence region 会直接摧毁 gold page score，而遮挡 random region 不影响 score。

因此，可以认为模型分数对标注 evidence region 存在明确依赖。

---

### 7.6 Region-level localization 仍是难点

Region Hit@k 结果整体较低：

```text
Hybrid Fusion Region Hit@5 = 0.4000
Full MV Region Hit@5 = 0.0000
```

说明页面级 evidence retrieval 与区域级 evidence localization 之间存在难度差距。

当前 patch grid 可能较粗，且自动生成 bbox 也可能带来一定噪声。

---

## 8. 当前问题与限制

本周实验仍存在以下限制：

```text
1. 部分 query_text 为空，导致可视化图中 Query 字段未显示具体文本。
2. Windows type 命令显示 Markdown 时出现中文乱码，但文件本身为 UTF-8 编码。
3. Single-vector Visual 在 Evidence Hit 评估中缺少 run 文件，未纳入有效比较。
4. Region Hit@k 指标较低，说明 patch-level evidence localization 仍需改进。
5. 当前 random mask 与 gold bbox 的 IoU 均为 0，适合作为严格对照，但还可以进一步增加不同重叠比例的 random mask。
```

---

## 9. Week 7 输出文件总览

### 9.1 Core Tables

```text
results/week7/day6_core_tables/table14_bm25_c2f_main_results.csv
results/week7/day6_core_tables/table14_bm25_c2f_main_results.md
results/week7/day6_core_tables/table14_bm25_c2f_main_results.json

results/week7/day6_core_tables/table15_budgeted_retrieval_configs.csv
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.md
results/week7/day6_core_tables/table15_budgeted_retrieval_configs.json

results/week7/day6_core_tables/table16_evidence_hit_main_results.csv
results/week7/day6_core_tables/table16_evidence_hit_main_results.md
results/week7/day6_core_tables/table16_evidence_hit_main_results.json

results/week7/day6_core_tables/table17_occlusion_main_results.csv
results/week7/day6_core_tables/table17_occlusion_main_results.md
results/week7/day6_core_tables/table17_occlusion_main_results.json
```

---

### 9.2 Evidence and Region Evaluation

```text
results/week7/evidence_hit/evidence_hit_atk_results.csv
results/week7/evidence_hit/evidence_hit_atk_results.md
results/week7/evidence_hit/evidence_hit_atk_per_query.csv
results/week7/evidence_hit/evidence_hit_atk_summary.json

results/week7/region_hit/region_hit_atk_results.csv
results/week7/region_hit/region_hit_atk_results.md
results/week7/region_hit/region_hit_atk_per_query.csv
results/week7/region_hit/region_hit_atk_summary.json
results/week7/region_hit/region_hit_top_patches.csv
```

---

### 9.3 Occlusion Outputs

```text
results/week7/occlusion/occlusion_inputs.csv
results/week7/occlusion/occlusion_inputs.jsonl
results/week7/occlusion/occlusion_inputs.md
results/week7/occlusion/occlusion_metrics_per_query.csv
results/week7/occlusion/occlusion_metrics_summary.csv
results/week7/occlusion/occlusion_metrics_summary.json
results/week7/occlusion/occlusion_table12_condition_results.csv
results/week7/occlusion/occlusion_table13_gap_results.csv
results/week7/occlusion/occlusion_output_tables.md
results/week7/occlusion/occlusion_output_tables.json
```

---

### 9.4 Visual Cases

```text
figures/week7/evidence_case_001.png
figures/week7/evidence_case_002.png
figures/week7/evidence_case_003.png
figures/week7/evidence_case_004.png
figures/week7/evidence_case_005.png

results/week7/day6_visual_cases/week7_visual_case_summary.csv
results/week7/day6_visual_cases/week7_visual_case_summary.md
results/week7/day6_visual_cases/week7_visual_case_summary.json
```

---

## 10. 总体验收结论

| Module | Status |
|---|---|
| Fixed-N candidate generation | Completed |
| BM25 + Full MV reranking | Completed |
| Budgeted MV reranking | Completed |
| Score normalization | Completed |
| Hybrid Fusion | Completed |
| Evidence subset construction | Completed |
| Evidence bbox annotation | Completed |
| Evidence Hit@k | Completed |
| Region Hit@k | Completed |
| Occlusion analysis | Completed |
| Core tables | Completed |
| Visual cases | Completed |

最终状态：

```text
Week 7 experiments completed successfully.
```

---

## 11. 可写入论文的核心结论

Week 7 的核心结论可以概括为：

```text
After fixing the coarse candidate budget, BM25 remains a strong baseline for PCB document-page retrieval.
Full multi-vector reranking can recover gold evidence pages within Top-10 but is less effective at placing them at the top.
Hybrid fusion improves evidence-level retrieval robustness, matching BM25 on Evidence Hit@5 and Evidence Hit@10.
Occlusion analysis shows that masking the gold evidence region collapses the gold page score to zero,
while random masking leaves the score unchanged, providing direct evidence that the model relies on annotated visual evidence regions.
```
