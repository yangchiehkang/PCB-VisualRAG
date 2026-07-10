# Week 5 Day 3 Token Budget Retrieval Experiment Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Day:** Day 3  
**Date:** 2026-05-07  
**Experiment Name:** Formal Retrieval Evaluation under Different Token Budgets  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是运行不同 token budget M 下的正式检索实验，并输出统一评测结果。

本日重点包括：

1. 对全部页面生成不同 M 下的 compressed page embeddings；
2. 固定 Week 4 中表现稳定的候选页面数 N；
3. 对不同 M 执行 C2F reranking；
4. 输出标准 run 文件；
5. 统一计算 Recall@1、Recall@5、Recall@10、MRR@10 和 nDCG@10；
6. 生成 token budget 对比表；
7. 分析不同 token 数量对检索质量和延迟的影响。

---

## 2. 实验设置

### 2.1 固定候选页面数

今日实验固定候选页面数为：

```text
N = 10
```

候选文件为：

```text
artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv
```

该候选文件包含：

| 项目 | 数量 |
|---|---:|
| Query Count | 30 |
| Candidate Rows | 300 |
| Avg Candidates / Query | 10 |

---

### 2.2 Token Budget 设置

由于当前 page multi-vector embedding 的 shape 为：

```text
(49, 512)
```

因此每页原始 token 数为：

```text
49
```

本日正式实验使用以下 M：

| M | 说明 |
|---:|---|
| 8 | 极强 token 压缩 |
| 16 | 轻量 token 压缩 |
| 24 | 中等 token 压缩 |
| 32 | 较高质量 token 压缩 |
| 49 | Full-token setting |

说明：

- 原计划中的 M64、M128、M256 不适用于当前实验；
- 因为当前每页最多只有 49 个 page tokens；
- 因此 M49 即为 full-token setting；
- 本日重点比较 M8、M16、M24、M32、M49 的检索效果变化。

---

## 3. 今日执行流程

### 3.1 生成全量 compressed page embeddings

执行命令：

```bat
python scripts\compression\select_page_tokens_norm.py --max-pages 0
```

输出信息：

```text
[Done] Token selection completed.
[Output] results\budgeted\token_selection\day2_validation\day2_token_selection_summary.csv
[Output] results\budgeted\token_selection\day2_validation\day2_token_selection_metadata_all.csv
```

生成的 compressed embedding 目录包括：

```text
artifacts\embeddings\token_selection\pages_M8
artifacts\embeddings\token_selection\pages_M16
artifacts\embeddings\token_selection\pages_M24
artifacts\embeddings\token_selection\pages_M32
artifacts\embeddings\token_selection\pages_M49
```

---

### 3.2 全量 compressed embeddings 检查

检查每个 M 目录下的 page embedding 文件数量：

| M | 文件数量 |
|---:|---:|
| 8 | 101 |
| 16 | 101 |
| 24 | 101 |
| 32 | 101 |
| 49 | 101 |

检查结果说明：

1. 五个 M 设置下均生成了 101 个 page embeddings；
2. 不同 M 的 page 数量一致；
3. 全量 compressed embeddings 已准备完成；
4. 正式 reranking 所需页面均可被正常加载。

示例检查文件：

```text
artifacts\embeddings\token_selection\pages_M8\doc003_p004.npy
```

该文件存在，说明之前缺失的页面已经成功补齐。

---

## 4. 正式 C2F Reranking 实验

### 4.1 执行命令

执行：

```bat
python scripts\retrieval\run_token_budget_c2f_rerank.py
```

脚本使用设置：

| 项目 | 设置 |
|---|---|
| Candidate File | `artifacts\rerank_cache\single_vector_topN\single_vector_candidates_top10.tsv` |
| Query Count | 30 |
| Candidate Rows | 300 |
| M List | 8, 16, 24, 32, 49 |
| Fixed N | 10 |

---

### 4.2 Reranking 输出结果

终端输出显示所有 M 均成功完成：

```text
[Done] c2f_N10_M8
[Done] c2f_N10_M16
[Done] c2f_N10_M24
[Done] c2f_N10_M32
[Done] c2f_N10_M49
[Done] All token-budget reranking completed.
```

生成 latency summary：

```text
results\budgeted\token_selection\summary\token_budget_day3_latency_by_M.csv
```

---

## 5. Day 3 生成文件

### 5.1 Run 文件

今日生成以下 run 文件：

| M | Run File |
|---:|---|
| 8 | `results\budgeted\token_selection\c2f_N10_M8_run.tsv` |
| 16 | `results\budgeted\token_selection\c2f_N10_M16_run.tsv` |
| 24 | `results\budgeted\token_selection\c2f_N10_M24_run.tsv` |
| 32 | `results\budgeted\token_selection\c2f_N10_M32_run.tsv` |
| 49 | `results\budgeted\token_selection\c2f_N10_M49_run.tsv` |

---

### 5.2 Score 文件

今日生成以下 score 文件：

| M | Score File |
|---:|---|
| 8 | `results\budgeted\token_selection\c2f_N10_M8_scores.csv` |
| 16 | `results\budgeted\token_selection\c2f_N10_M16_scores.csv` |
| 24 | `results\budgeted\token_selection\c2f_N10_M24_scores.csv` |
| 32 | `results\budgeted\token_selection\c2f_N10_M32_scores.csv` |
| 49 | `results\budgeted\token_selection\c2f_N10_M49_scores.csv` |

---

### 5.3 Validation 文件

今日生成以下 validation 文件：

| M | Validation File |
|---:|---|
| 8 | `results\budgeted\token_selection\c2f_N10_M8_validation.csv` |
| 16 | `results\budgeted\token_selection\c2f_N10_M16_validation.csv` |
| 24 | `results\budgeted\token_selection\c2f_N10_M24_validation.csv` |
| 32 | `results\budgeted\token_selection\c2f_N10_M32_validation.csv` |
| 49 | `results\budgeted\token_selection\c2f_N10_M49_validation.csv` |

---

### 5.4 Summary 文件

今日生成以下 summary 文件：

| 文件 | 路径 |
|---|---|
| Latency summary | `results\budgeted\token_selection\summary\token_budget_day3_latency_by_M.csv` |
| Metrics CSV | `results\budgeted\token_selection\summary\token_budget_metrics.csv` |
| Metrics Excel | `results\budgeted\token_selection\summary\token_budget_metrics.xlsx` |
| Initial comparison Markdown | `results\budgeted\token_selection\summary\token_budget_initial_comparison.md` |

---

## 6. 统一评测结果

### 6.1 评测命令

执行：

```bat
python scripts\evaluation\evaluate_token_budget_day3.py
```

输出信息：

```text
[Done] Token budget evaluation completed.
[Output] results\budgeted\token_selection\summary\token_budget_metrics.csv
[Output] results\budgeted\token_selection\summary\token_budget_metrics.xlsx
[Output] results\budgeted\token_selection\summary\token_budget_initial_comparison.md
```

---

### 6.2 Token Budget Metrics

今日最终评测结果如下：

| Method | M | Evaluated Queries | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency ms/query | Avg Candidates / Query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full Multi-vector | full | 30 | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 | N/A | N/A |
| Week4 C2F N10 | 49 | 30 | 0.0333 | 0.0333 | 0.2667 | 0.0628 | 0.1033 | N/A | N/A |
| C2F N10 M8 | 8 | 30 | 0.0667 | 0.0667 | 0.2667 | 0.0907 | 0.1249 | 2.0249 | 10 |
| C2F N10 M16 | 16 | 30 | 0.0667 | 0.0667 | 0.2667 | 0.0901 | 0.1242 | 1.6379 | 10 |
| C2F N10 M24 | 24 | 30 | 0.0333 | 0.1000 | 0.2667 | 0.0754 | 0.1145 | 1.6846 | 10 |
| C2F N10 M32 | 32 | 30 | 0.0000 | 0.1000 | 0.2667 | 0.0465 | 0.0920 | 1.8168 | 10 |
| C2F N10 M49 | 49 | 30 | 0.0333 | 0.0333 | 0.2667 | 0.0628 | 0.1033 | 2.3857 | 10 |

---

## 7. 结果分析

### 7.1 M49 与 Week4 C2F N10 完全一致

从结果看：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Week4 C2F N10 | 0.0333 | 0.0333 | 0.2667 | 0.0628 | 0.1033 |
| C2F N10 M49 | 0.0333 | 0.0333 | 0.2667 | 0.0628 | 0.1033 |

这说明：

1. M49 作为 full-token setting，与 Week4 C2F N10 的结果完全一致；
2. Day 3 的 reranking pipeline 是可靠的；
3. token selection 版本在 M49 下没有引入额外误差；
4. compressed embedding 生成、加载、scoring 和 evaluation 流程均正常。

这是今天最关键的 sanity check。

---

### 7.2 不同 M 下 Recall@10 均保持一致

不同 token budget 下，C2F N10 的 Recall@10 都是：

```text
0.2667
```

对应结果：

| Method | M | Recall@10 |
|---|---:|---:|
| C2F N10 M8 | 8 | 0.2667 |
| C2F N10 M16 | 16 | 0.2667 |
| C2F N10 M24 | 24 | 0.2667 |
| C2F N10 M32 | 32 | 0.2667 |
| C2F N10 M49 | 49 | 0.2667 |

这说明：

1. 在固定 N=10 的候选集合内，即使只保留很少 tokens，也能保留相同的 top-10 命中能力；
2. token selection 对候选集合内的 Recall@10 没有造成下降；
3. 对当前 30 个 queries 和 101 个 pages 的小规模数据而言，Recall@10 对 token 数变化不敏感；
4. 真正受 token budget 影响更明显的是排序质量，而不是 top-10 是否命中。

---

### 7.3 M8 和 M16 的排序指标反而最好

在 C2F token budget 实验中，M8 和 M16 的 MRR@10 与 nDCG@10 最高：

| Method | M | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| C2F N10 M8 | 8 | 0.0907 | 0.1249 |
| C2F N10 M16 | 16 | 0.0901 | 0.1242 |
| C2F N10 M24 | 24 | 0.0754 | 0.1145 |
| C2F N10 M49 | 49 | 0.0628 | 0.1033 |
| C2F N10 M32 | 32 | 0.0465 | 0.0920 |

这说明：

1. 较小的 M 并没有简单导致性能下降；
2. Norm-based token selection 可能过滤掉了一部分对当前 query 不重要甚至有噪声的 page tokens；
3. 在当前数据集上，M8 和 M16 保留的高 norm tokens 对排序更有帮助；
4. token 压缩在某些情况下可能具有一定的去噪效果。

需要注意的是，当前评测 query 数为 30，数据规模较小，因此该趋势需要在后续更大规模实验或更多 queries 上继续验证。

---

### 7.4 M32 的表现低于预期

M32 的结果为：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| C2F N10 M32 | 0.0000 | 0.1000 | 0.2667 | 0.0465 | 0.0920 |

观察：

1. M32 的 Recall@10 仍然保持 0.2667；
2. 但 Recall@1 降为 0；
3. MRR@10 和 nDCG@10 低于 M8、M16、M24 和 M49；
4. 说明 M32 能把相关页面保留在 top-10 内，但排序位置不理想。

可能原因：

- M32 引入了一些额外 tokens，改变了 late interaction 的最大相似度结构；
- 新增 tokens 不一定都是有帮助的，可能会影响 page 间相对排序；
- norm-based selection 是 query-independent 方法，未必对所有 query 都最优；
- 小规模数据下，少数 query 的排序变化会明显影响 MRR 和 nDCG。

---

### 7.5 M49 与 Full Multi-vector 的关系

结果显示：

| Method | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| Full Multi-vector | 0.1333 | 0.0644 | 0.0807 |
| C2F N10 M49 | 0.2667 | 0.0628 | 0.1033 |

观察：

1. C2F N10 M49 的 Recall@10 高于 Full Multi-vector；
2. MRR@10 与 Full Multi-vector 接近；
3. nDCG@10 高于 Full Multi-vector；
4. 这说明在当前实验设置下，Week4 的 candidate filtering 加 C2F reranking 组合具有较好的 top-10 覆盖效果。

需要注意：

- Full Multi-vector 与 C2F N10 的检索流程可能不是完全相同的候选来源和排序流程；
- 因此两者更适合作为系统级对比，而不是纯粹的 token budget 对比；
- Token budget 内部最可靠的对比对象是 M8、M16、M24、M32、M49 之间的变化。

---

## 8. 延迟分析

### 8.1 不同 M 的 reranking latency

| Method | M | Latency ms/query |
|---|---:|---:|
| C2F N10 M8 | 8 | 2.0249 |
| C2F N10 M16 | 16 | 1.6379 |
| C2F N10 M24 | 24 | 1.6846 |
| C2F N10 M32 | 32 | 1.8168 |
| C2F N10 M49 | 49 | 2.3857 |

观察：

1. M49 的 latency 最高，为 2.3857 ms/query；
2. M16 的 latency 最低，为 1.6379 ms/query；
3. 从 M16 到 M49，整体 latency 有上升趋势；
4. M8 比 M16 慢，可能受到 Python 循环、文件读取、缓存和小规模计时波动影响；
5. 当前每个 query 只有 10 个候选，因此 latency 数值整体很小，不能过度解读细微差异。

总体来看，减少 page tokens 可以降低 reranking 计算开销，尤其 M16、M24、M32 相比 M49 具有更低延迟。

---

### 8.2 M16 的效率质量 trade-off 最突出

M16 的结果为：

| Metric | Value |
|---|---:|
| Recall@1 | 0.0667 |
| Recall@5 | 0.0667 |
| Recall@10 | 0.2667 |
| MRR@10 | 0.0901 |
| nDCG@10 | 0.1242 |
| Latency ms/query | 1.6379 |

M16 的特点：

1. Recall@10 与 M49 持平；
2. MRR@10 明显高于 M49；
3. nDCG@10 明显高于 M49；
4. latency 明显低于 M49；
5. token 数只保留 16 个，约为 full-token 的三分之一。

因此，在当前实验中，M16 是一个很强的 efficiency-quality trade-off 配置。

---

## 9. 今日关键发现

今日实验得到以下关键发现：

1. M49 与 Week4 C2F N10 结果完全一致，验证了 Day 3 pipeline 的正确性；
2. 在固定 N=10 下，M8、M16、M24、M32、M49 的 Recall@10 均为 0.2667；
3. M8 和 M16 在 MRR@10 与 nDCG@10 上表现最好；
4. M32 的 Recall@10 保持不变，但排序质量下降；
5. Token selection 没有造成 top-10 命中能力下降；
6. 较小 M 在当前数据上可能产生去噪效果；
7. M16 在质量和延迟之间取得了最好的平衡；
8. M49 的 latency 最高，符合 full-token reranking 计算量更大的预期。

---

## 10. 今日验收情况

| 验收项 | 状态 |
|---|---|
| 全量 compressed embeddings 已生成 | Completed |
| M8/M16/M24/M32/M49 文件数一致 | Completed |
| 固定 N=10 的 reranking 已完成 | Completed |
| 不同 M 的 run 文件已生成 | Completed |
| 不同 M 的 score 文件已生成 | Completed |
| 不同 M 的 validation 文件已生成 | Completed |
| latency summary 已生成 | Completed |
| token_budget_metrics.csv 已生成 | Completed |
| token_budget_metrics.xlsx 已生成 | Completed |
| token_budget_initial_comparison.md 已生成 | Completed |
| 与 Full MV / Week4 C2F 初步对比已完成 | Completed |

---

## 11. 今日结论

Week 5 Day 3 已完成不同 token budget M 下的正式 C2F reranking 实验。

今日固定候选页面数 N=10，并分别评测了 M=8、M=16、M=24、M=32 和 M=49 下的检索质量。实验共覆盖 30 个 queries、300 条候选记录和 101 个 page embeddings。

最终结果显示：

1. M49 与 Week4 C2F N10 指标完全一致，说明实验管线可靠；
2. 所有 token budget 设置下 Recall@10 均保持 0.2667；
3. M8 和 M16 在 MRR@10 与 nDCG@10 上优于 M49；
4. M16 同时具有较低 latency 和较高排序质量，是当前最优 trade-off 配置；
5. Norm-based token selection 在当前数据上不仅没有破坏 Recall@10，还可能通过去除部分低价值 tokens 改善排序质量。

最终判断：

> Day 3 验收通过。当前已经获得 Week 5 最重要的一批结果：不同 token budget M 下的检索质量、排序表现和延迟变化。当前结果支持继续进入 Day 4，对 token budget 结果进行可视化、拐点分析和质量-效率 trade-off 总结。
