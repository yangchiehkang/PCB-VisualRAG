# Week 7 Day 3 实验日志：Score Normalization 与 Hybrid Fusion

**日期**：2026-05-08  
**项目**：PCB_VisualRAG_Project  
**环境**：`pcb_visualrag`  
**工作目录**：`E:\Working\PCB_VisualRAG_Project`

---

## Task 1：BM25 score 与 MV score 分数归一化

### 1. 实验目标

本任务对每个 query 内的 BM25 score 与 MV score 分别进行 min-max normalization。

归一化公式为：

$$
Score_{norm} = \frac{Score - \min(Score)}{\max(Score) - \min(Score) + \epsilon}
$$

其中：

- BM25 score 使用 `coarse_score`；
- MV score 使用 `fine_score`；
- 每个 query 内独立归一化；
- 输出 `bm25_score_norm` 与 `mv_score_norm`。

---

### 2. 执行命令

删除旧结果目录：

```bash
rmdir /s /q results\week7\score_normalized
```

系统提示：

```text
系统找不到指定的文件。
```

该提示表示旧目录不存在，属于正常情况。

运行归一化脚本：

```bash
python scripts\evaluation\normalize_week7_bm25_mv_scores.py
```

---

### 3. 运行结果

终端输出摘要：

```text
[Week7-Day3] Starting score normalization...
[Week7-Day3] Normalizing fullmv_N10 ...
[Week7-Day3] fullmv_N10 done. queries=30, rows=300, avg_candidates=10.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing fullmv_N20 ...
[Week7-Day3] fullmv_N20 done. queries=30, rows=600, avg_candidates=20.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing fullmv_N50 ...
[Week7-Day3] fullmv_N50 done. queries=30, rows=1500, avg_candidates=50.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing fullmv_N100 ...
[Week7-Day3] fullmv_N100 done. queries=30, rows=3000, avg_candidates=100.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing budgetmv_N20_M8_none ...
[Week7-Day3] budgetmv_N20_M8_none done. queries=30, rows=600, avg_candidates=20.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing budgetmv_N20_M16_none ...
[Week7-Day3] budgetmv_N20_M16_none done. queries=30, rows=600, avg_candidates=20.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
[Week7-Day3] Normalizing budgetmv_N50_M24_none ...
[Week7-Day3] budgetmv_N50_M24_none done. queries=30, rows=1500, avg_candidates=50.0000, bm25_norm=[0.0000,1.0000], mv_norm=[0.0000,1.0000], status=PASSED
```

---

### 4. 输出文件检查

执行命令：

```bash
dir results\week7\score_normalized
```

生成文件：

```text
bm25_budgetmv_N20_M16_none_normalized_scores.csv
bm25_budgetmv_N20_M8_none_normalized_scores.csv
bm25_budgetmv_N50_M24_none_normalized_scores.csv
bm25_fullmv_N100_normalized_scores.csv
bm25_fullmv_N10_normalized_scores.csv
bm25_fullmv_N20_normalized_scores.csv
bm25_fullmv_N50_normalized_scores.csv
score_normalization_summary.csv
score_normalization_summary.json
```

共生成：

```text
9 个文件
```

---

### 5. Summary 结果

执行命令：

```bash
type results\week7\score_normalized\score_normalization_summary.csv
```

整理结果如下：

| Method | Setting | Queries | Rows | Avg Candidates / Query | BM25 Norm Min | BM25 Norm Max | MV Norm Min | MV Norm Max | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| fullmv | fullmv_N10 | 30 | 300 | 10.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 0.99999999 | PASSED |
| fullmv | fullmv_N20 | 30 | 600 | 20.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 0.99999999 | PASSED |
| fullmv | fullmv_N50 | 30 | 1500 | 50.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 1.00000000 | PASSED |
| fullmv | fullmv_N100 | 30 | 3000 | 100.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 1.00000000 | PASSED |
| budgetmv | budgetmv_N20_M8_none | 30 | 600 | 20.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 0.99999999 | PASSED |
| budgetmv | budgetmv_N20_M16_none | 30 | 600 | 20.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 0.99999999 | PASSED |
| budgetmv | budgetmv_N50_M24_none | 30 | 1500 | 50.0000 | 0.00000000 | 1.00000000 | 0.00000000 | 0.99999999 | PASSED |

---

### 6. FAILED 检查

执行命令：

```bash
findstr /I "FAILED" results\week7\score_normalized\score_normalization_summary.csv
```

结果无输出，说明全部配置通过检查。

---

### 7. Task 1 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| Full MV 四组 score 文件完成归一化 | N=10、20、50、100 均完成 | Passed |
| Budgeted MV 三组 score 文件完成归一化 | N20-M8、N20-M16、N50-M24 均完成 | Passed |
| 每个 query 内 BM25 score 归一化 | 范围均在 0–1 | Passed |
| 每个 query 内 MV score 归一化 | 范围均在 0–1 | Passed |
| summary 文件生成 | CSV 与 JSON 均生成 | Passed |
| status 全部为 PASSED | 无 FAILED | Passed |

最终结论：

```text
Week 7 Day 3 Task 1 Status: PASS
```

---

## Task 2：Hybrid Fusion Rerank

### 1. 实验目标

本任务在 BM25 top-N candidate 中，对归一化后的 BM25 score 与 MV score 进行融合排序。

本轮固定：

$$
N = 50
$$

Hybrid score 定义为：

$$
Score_{hybrid} = \alpha \cdot Score_{BM25,norm} + (1 - \alpha) \cdot Score_{MV,norm}
$$

测试 alpha 范围：

```text
0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
```

测试对象：

| Method | Setting | N | M |
|---|---|---:|---:|
| Hybrid Full MV | fullmv_N50 | 50 | - |
| Hybrid Budgeted MV | budgetmv_N50_M24_none | 50 | 24 |

---

### 2. 执行命令

删除旧结果目录：

```bash
rmdir /s /q results\week7\hybrid_fusion
```

系统提示：

```text
系统找不到指定的文件。
```

该提示表示旧目录不存在，属于正常情况。

运行 hybrid fusion：

```bash
python scripts\retrieval\run_week7_hybrid_fusion_rerank.py
```

---

### 3. 运行结果摘要

Full MV N=50 的 alpha sweep 全部完成：

```text
alpha=0.0 到 alpha=1.0
queries=30
candidates=1500
written=300
status=PASSED
```

Budgeted MV N=50 M=24 的 alpha sweep 全部完成：

```text
alpha=0.0 到 alpha=1.0
queries=30
candidates=1500
written=300
status=PASSED
```

---

### 4. 输出文件检查

执行命令：

```bash
dir results\week7\hybrid_fusion\*_run.tsv /b
```

生成 run 文件：

```text
hybrid_budgetmv_N50_M24_alpha0p0_run.tsv
hybrid_budgetmv_N50_M24_alpha0p1_run.tsv
hybrid_budgetmv_N50_M24_alpha0p2_run.tsv
hybrid_budgetmv_N50_M24_alpha0p3_run.tsv
hybrid_budgetmv_N50_M24_alpha0p4_run.tsv
hybrid_budgetmv_N50_M24_alpha0p5_run.tsv
hybrid_budgetmv_N50_M24_alpha0p6_run.tsv
hybrid_budgetmv_N50_M24_alpha0p7_run.tsv
hybrid_budgetmv_N50_M24_alpha0p8_run.tsv
hybrid_budgetmv_N50_M24_alpha0p9_run.tsv
hybrid_budgetmv_N50_M24_alpha1p0_run.tsv
hybrid_fullmv_N50_alpha0p0_run.tsv
hybrid_fullmv_N50_alpha0p1_run.tsv
hybrid_fullmv_N50_alpha0p2_run.tsv
hybrid_fullmv_N50_alpha0p3_run.tsv
hybrid_fullmv_N50_alpha0p4_run.tsv
hybrid_fullmv_N50_alpha0p5_run.tsv
hybrid_fullmv_N50_alpha0p6_run.tsv
hybrid_fullmv_N50_alpha0p7_run.tsv
hybrid_fullmv_N50_alpha0p8_run.tsv
hybrid_fullmv_N50_alpha0p9_run.tsv
hybrid_fullmv_N50_alpha1p0_run.tsv
```

共生成：

```text
22 个 run 文件
```

---

### 5. Run 文件行数检查

执行命令：

```bash
find /c /v "" results\week7\hybrid_fusion\hybrid_fullmv_N50_alpha0p5_run.tsv
find /c /v "" results\week7\hybrid_fusion\hybrid_budgetmv_N50_M24_alpha0p5_run.tsv
```

检查结果：

```text
hybrid_fullmv_N50_alpha0p5_run.tsv: 301
hybrid_budgetmv_N50_M24_alpha0p5_run.tsv: 301
```

由于共有 30 个 queries，每个 query 输出 top-10，并包含 1 行 header，因此预期行数为：

$$
30 \times 10 + 1 = 301
$$

实际结果符合预期。

---

### 6. Validation 检查

执行命令：

```bash
findstr /I "FAILED" results\week7\hybrid_fusion\*_validation.csv
```

结果无输出，说明全部 fusion validation 通过。

---

### 7. Fusion Summary

执行命令：

```bash
type results\week7\hybrid_fusion\hybrid_fusion_summary.csv
```

summary 关键结论：

| Method | Setting | N | M | Alpha Count | Queries | Candidates / Run | Written / Run | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| fullmv | fullmv_N50 | 50 | - | 11 | 30 | 1500 | 300 | PASSED |
| budgetmv | budgetmv_N50_M24_none | 50 | 24 | 11 | 30 | 1500 | 300 | PASSED |

融合排序本身的平均耗时约为：

```text
0.12–0.16 ms/query
```

该耗时仅包含融合分数计算与排序，不包含前序 BM25 / MV embedding scoring。

---

### 8. Task 2 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| Full MV N=50 完成 11 个 alpha fusion | alpha=0.0–1.0 | Passed |
| Budgeted MV N=50 M=24 完成 11 个 alpha fusion | alpha=0.0–1.0 | Passed |
| 每个 run 文件输出 top-10 | 抽查均为 301 行 | Passed |
| validation 无 FAILED | 无输出 | Passed |
| summary 文件生成 | CSV 与 JSON 均生成 | Passed |
| status 全部为 PASSED | 已确认 | Passed |

最终结论：

```text
Week 7 Day 3 Task 2 Status: PASS
```

---

## Task 3：Hybrid Fusion Alpha Ablation

### 1. 实验目标

本任务对 Task 2 生成的 hybrid fusion run 文件进行评估，搜索最佳 alpha，并输出 alpha 消融表。

评估指标：

```text
Recall@1
Recall@5
Recall@10
MRR@10
nDCG@10
```

重点输出 alpha：

```text
0.2, 0.4, 0.6, 0.8
```

---

### 2. 执行命令

运行过程中前两次提示脚本文件不存在：

```text
python: can't open file 'E:\Working\PCB_VisualRAG_Project\scripts\evaluation\evaluate_week7_hybrid_alpha_ablation.py': [Errno 2] No such file or directory
```

随后补齐脚本后重新运行成功：

```bash
python scripts\evaluation\evaluate_week7_hybrid_alpha_ablation.py
```

---

### 3. 全部 alpha 评估结果

终端输出：

```text
========== Hybrid Alpha All Results ==========
Method,Alpha,Recall@1,Recall@5,Recall@10,MRR@10,nDCG@10
Hybrid Full MV N=50,0.0,0.0667,0.1000,0.1333,0.0881,0.0988
Hybrid Full MV N=50,0.1,0.0667,0.1333,0.1667,0.0992,0.1155
Hybrid Full MV N=50,0.2,0.0667,0.2000,0.2000,0.1278,0.1464
Hybrid Full MV N=50,0.3,0.0667,0.3000,0.4333,0.1675,0.2289
Hybrid Full MV N=50,0.4,0.1333,0.4000,0.6167,0.2555,0.3389
Hybrid Full MV N=50,0.5,0.2333,0.5833,0.6833,0.3649,0.4399
Hybrid Full MV N=50,0.6,0.2333,0.6500,0.7500,0.3971,0.4803
Hybrid Full MV N=50,0.7,0.2333,0.6833,0.7500,0.4356,0.5113
Hybrid Full MV N=50,0.8,0.1667,0.6833,0.7667,0.4056,0.4926
Hybrid Full MV N=50,0.9,0.1333,0.6833,0.8167,0.4038,0.5048
Hybrid Full MV N=50,1.0,0.1333,0.6833,0.8833,0.4105,0.5241
Hybrid Budgeted MV N=50 M=24,0.0,0.0000,0.0333,0.1000,0.0170,0.0359
Hybrid Budgeted MV N=50 M=24,0.1,0.0000,0.1000,0.2000,0.0448,0.0804
Hybrid Budgeted MV N=50 M=24,0.2,0.0333,0.1667,0.3333,0.0931,0.1474
Hybrid Budgeted MV N=50 M=24,0.3,0.1000,0.3333,0.4000,0.1979,0.2465
Hybrid Budgeted MV N=50 M=24,0.4,0.2000,0.4333,0.5000,0.2903,0.3408
Hybrid Budgeted MV N=50 M=24,0.5,0.3000,0.5000,0.6333,0.3846,0.4432
Hybrid Budgeted MV N=50 M=24,0.6,0.2000,0.6333,0.7000,0.3909,0.4674
Hybrid Budgeted MV N=50 M=24,0.7,0.1333,0.6667,0.7333,0.3728,0.4630
Hybrid Budgeted MV N=50 M=24,0.8,0.1667,0.6833,0.8000,0.4112,0.5054
Hybrid Budgeted MV N=50 M=24,0.9,0.1333,0.6833,0.8333,0.4087,0.5099
Hybrid Budgeted MV N=50 M=24,1.0,0.1333,0.6833,0.8833,0.4105,0.5241
```

---

### 4. Alpha 消融表

执行命令：

```bash
type results\week7\hybrid_fusion\hybrid_alpha_ablation_table.csv
```

整理结果如下：

| Method | Alpha | Recall@1 | Recall@5 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Hybrid Full MV N=50 | 0.2 | 0.0667 | 0.2000 | 0.2000 | 0.1464 |
| Hybrid Full MV N=50 | 0.4 | 0.1333 | 0.4000 | 0.6167 | 0.3389 |
| Hybrid Full MV N=50 | 0.6 | 0.2333 | 0.6500 | 0.7500 | 0.4803 |
| Hybrid Full MV N=50 | 0.8 | 0.1667 | 0.6833 | 0.7667 | 0.4926 |
| Hybrid Budgeted MV N=50 M=24 | 0.2 | 0.0333 | 0.1667 | 0.3333 | 0.1474 |
| Hybrid Budgeted MV N=50 M=24 | 0.4 | 0.2000 | 0.4333 | 0.5000 | 0.3408 |
| Hybrid Budgeted MV N=50 M=24 | 0.6 | 0.2000 | 0.6333 | 0.7000 | 0.4674 |
| Hybrid Budgeted MV N=50 M=24 | 0.8 | 0.1667 | 0.6833 | 0.8000 | 0.5054 |

---

### 5. 最佳 alpha 结果

执行命令：

```bash
type results\week7\hybrid_fusion\hybrid_alpha_best_results.csv
```

结果：

| Method | Setting | Best Alpha | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Queries |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Hybrid Full MV N=50 | hybrid_fullmv_N50 | 1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | 30 |
| Hybrid Budgeted MV N=50 M=24 | hybrid_budgetmv_N50_M24 | 1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 | 30 |

最佳 alpha 均为：

```text
alpha = 1.0
```

这表示在当前实验配置下，完全依赖 BM25 score 的排序结果最佳。

---

### 6. 输出文件检查

执行命令：

```bash
dir results\week7\hybrid_fusion\hybrid_alpha*
```

生成文件：

```text
hybrid_alpha_ablation_table.csv
hybrid_alpha_ablation_table.md
hybrid_alpha_all_results.csv
hybrid_alpha_best_results.csv
hybrid_alpha_best_results.json
```

共生成：

```text
5 个文件
```

---

### 7. Task 3 结果分析

#### 7.1 Full MV Hybrid 趋势

Hybrid Full MV N=50 随 alpha 增大，整体性能逐渐接近 BM25 baseline。

| Alpha | Recall@10 | nDCG@10 |
|---:|---:|---:|
| 0.0 | 0.1333 | 0.0988 |
| 0.2 | 0.2000 | 0.1464 |
| 0.4 | 0.6167 | 0.3389 |
| 0.6 | 0.7500 | 0.4803 |
| 0.8 | 0.7667 | 0.4926 |
| 1.0 | 0.8833 | 0.5241 |

最佳结果：

```text
alpha=1.0
nDCG@10=0.5241
Recall@10=0.8833
```

---

#### 7.2 Budgeted MV Hybrid 趋势

Hybrid Budgeted MV N=50 M=24 同样随 alpha 增大而提升。

| Alpha | Recall@10 | nDCG@10 |
|---:|---:|---:|
| 0.0 | 0.1000 | 0.0359 |
| 0.2 | 0.3333 | 0.1474 |
| 0.4 | 0.5000 | 0.3408 |
| 0.6 | 0.7000 | 0.4674 |
| 0.8 | 0.8000 | 0.5054 |
| 1.0 | 0.8833 | 0.5241 |

最佳结果：

```text
alpha=1.0
nDCG@10=0.5241
Recall@10=0.8833
```

---

#### 7.3 主要观察

1. 当 alpha 较低时，MV score 权重较高，整体效果较差。
2. 随着 alpha 增大，BM25 score 权重增加，Recall@10 与 nDCG@10 持续提升。
3. alpha=1.0 时，hybrid fusion 等价于只使用 BM25 normalized score。
4. 当前 MV score 没有带来超过 BM25 的增益。
5. Budgeted MV 在 alpha=0.8 时达到较高结果：

```text
Recall@10=0.8000
nDCG@10=0.5054
```

但仍低于 alpha=1.0 的 BM25-only 结果：

```text
Recall@10=0.8833
nDCG@10=0.5241
```

---

### 8. Task 3 验收结论

| 验收项 | 结果 | 是否通过 |
|---|---|---|
| alpha=0.0–1.0 全量评估完成 | Full MV 与 Budgeted MV 均完成 | Passed |
| alpha 消融表生成 | CSV 与 Markdown 均生成 | Passed |
| 最佳 alpha 文件生成 | CSV 与 JSON 均生成 | Passed |
| 指标包含 Recall/MRR/nDCG | 已包含 | Passed |
| 最佳 alpha 输出 | alpha=1.0 | Passed |

最终结论：

```text
Week 7 Day 3 Task 3 Status: PASS
```

---

## Day 3 总体验收结论

本日完成任务如下：

| Task | 内容 | 状态 |
|---|---|---|
| Task 1 | BM25 与 MV score min-max normalization | PASS |
| Task 2 | Hybrid Fusion Rerank | PASS |
| Task 3 | Hybrid Fusion Alpha Ablation | PASS |

---

## Day 3 核心结果汇总

### 1. 分数归一化

| Setting | Rows | BM25 Norm Range | MV Norm Range | Status |
|---|---:|---|---|---|
| fullmv_N10 | 300 | 0–1 | 0–1 | PASSED |
| fullmv_N20 | 600 | 0–1 | 0–1 | PASSED |
| fullmv_N50 | 1500 | 0–1 | 0–1 | PASSED |
| fullmv_N100 | 3000 | 0–1 | 0–1 | PASSED |
| budgetmv_N20_M8_none | 600 | 0–1 | 0–1 | PASSED |
| budgetmv_N20_M16_none | 600 | 0–1 | 0–1 | PASSED |
| budgetmv_N50_M24_none | 1500 | 0–1 | 0–1 | PASSED |

---

### 2. Hybrid Fusion 最佳结果

| Method | Best Alpha | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| Hybrid Full MV N=50 | 1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |
| Hybrid Budgeted MV N=50 M=24 | 1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |

---

### 3. 与 BM25 baseline 对齐

Day 3 最佳结果与 Day 2 BM25 baseline 一致：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| BM25 baseline | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |
| Hybrid Full MV, alpha=1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |
| Hybrid Budgeted MV, alpha=1.0 | 0.1333 | 0.6833 | 0.8833 | 0.4105 | 0.5241 |

---

## Day 3 最终结论

```text
Week 7 Day 3 Overall Status: PASS
```

实验观察：

1. Score normalization 已成功完成，所有归一化分数均落在 0–1 范围内。
2. Hybrid fusion pipeline 正常工作，所有 alpha 配置均成功生成 run、score 与 validation 文件。
3. alpha ablation 表明：当前最佳 alpha 为 1.0。
4. alpha=1.0 等价于只使用 BM25 score，因此当前 MV score 未提供额外增益。
5. 随着 BM25 权重增加，检索指标稳定提升。
6. 后续优化重点应放在 MV score 质量、score calibration、query-type-aware fusion、以及 BM25+MV 非线性融合策略。
