# Week 4 Note：Coarse-to-Fine Retrieval 实验记录

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Date:** 2026-05-07  
**Topic:** Coarse-to-Fine Retrieval with Full Multi-vector Reranking  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 本周目标

Week 4 的目标是从 Week 3 的 Full Multi-vector Retrieval 进一步过渡到更具成本控制能力的 coarse-to-fine retrieval framework。

本周核心问题是：

> 是否可以先使用低成本 coarse retriever 召回少量候选页面，再仅在候选集合内执行 Full Multi-vector late interaction reranking，从而在尽量保持检索效果的同时降低计算成本？

本周重点包括：

- 设计 coarse-to-fine 两阶段检索流程；
- 使用 single-vector visual retrieval 作为 coarse retriever；
- 生成 N=10、20、50、100 的候选集合；
- 在候选集合内接入 Full Multi-vector reranker；
- 评测不同 N 下的 Recall@10、MRR@10、nDCG@10；
- 统计 rerank latency 和 actual candidates/query；
- 绘制第一版 quality-cost curve；
- 分析当前 best N 与失败模式；
- 为 Week 5 的 patch/token selection 提供依据。

---

## 2. 方法设计

Week 4 采用两阶段 coarse-to-fine retrieval pipeline。

流程如下：

    Query
      ↓
    Single-vector Visual Coarse Retriever
      ↓
    Top-N Candidate Pages
      ↓
    Full Multi-vector Late Interaction Reranker
      ↓
    Final Top-k Ranking
      ↓
    Evaluation + Cost Analysis

其中：

- **Coarse stage** 使用 Week 2 已经跑通的 single-vector visual retrieval；
- **Fine stage** 使用 Week 3 已经跑通的 Full Multi-vector Late Interaction reranker；
- **候选规模 N** 设定为 10、20、50、100；
- **评测指标** 包括 Recall@1、Recall@5、Recall@10、MRR@10、nDCG@10；
- **成本指标** 包括 rerank latency、actual candidates/query、rerank cost units。

本周实验重点不是训练新模型，而是验证：

> Full MV 是否可以从全库检索转化为候选集内 reranking，并形成可控的质量–成本折中。

---

## 3. Day-by-Day Progress

### 3.1 Day 1：Coarse-to-Fine Design

Day 1 完成了 Week 4 的整体实验设计。

主要工作包括：

- 明确 coarse-to-fine 两阶段检索框架；
- 确定 single-vector visual retrieval 作为 coarse retriever；
- 确定 Full Multi-vector late interaction 作为 fine reranker；
- 设定候选规模 N=10、20、50、100；
- 设计输入输出文件结构；
- 明确成本记录方式；
- 明确本周实验验收标准。

Day 1 的核心判断是：

> Full MV 全库检索成本较高，因此应通过 candidate budget control，将 Full MV 限制在少量候选页面内执行。

---

### 3.2 Day 2：Coarse Candidate Pipeline

Day 2 实现了 coarse candidate generation pipeline。

输入文件：

| 类型 | 路径 |
|---|---|
| Coarse run | `results/baselines/single_vector_visual_run.tsv` |
| Qrels | `data/metadata/qrels.tsv` |

输出文件：

| 类型 | 路径 |
|---|---|
| All candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_all.tsv` |
| Top-10 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv` |
| Top-20 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv` |
| Top-50 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv` |
| Top-100 candidates | `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv` |
| Coarse recall summary | `results/budgeted/coarse_to_fine/single_vector_coarse_recall.csv` |
| Coarse failure cases | `results/budgeted/coarse_to_fine/single_vector_coarse_failure_cases.csv` |

Coarse recall 统计结果如下：

| Candidate Depth | Evaluated Queries | Hit Queries | Miss Queries | Coarse Recall |
|---|---:|---:|---:|---:|
| Top-10 | 30 | 8 | 22 | 0.2667 |
| Top-20 | 30 | 8 | 22 | 0.2667 |
| Top-50 | 30 | 8 | 22 | 0.2667 |
| Top-100 | 30 | 8 | 22 | 0.2667 |

关键观察：

1. single-vector coarse retriever 的 coarse recall 为 0.2667；
2. 30 条 query 中只有 8 条在 coarse 阶段召回了 gold page；
3. Top-10、20、50、100 的 coarse recall 完全一致；
4. 这说明原始 single-vector visual run 很可能只保存了 top-10；
5. C2F 的最终效果上限受到 coarse recall 限制。

Day 2 结论：

> 当前 coarse retriever 是 Week 4 C2F pipeline 的主要瓶颈。如果 gold page 没有进入 coarse candidates，后续 Full MV reranker 无法恢复该 query。

---

### 3.3 Day 3：Full MV Reranking on Candidate Sets

Day 3 在 Day 2 生成的 candidates 上接入 Full MV reranker。

主要目标是验证：

- 每个 query 是否能正确读取候选页面；
- reranking 是否只发生在候选集合内；
- query embeddings 和 page embeddings 是否正常加载；
- late interaction scoring 是否正常执行；
- N=10、20、50、100 是否能分别输出 rerank run 文件。

主要输出文件如下：

| 类型 | 路径 |
|---|---|
| N=10 run | `results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv` |
| N=20 run | `results/budgeted/coarse_to_fine/c2f_single_vector_N20_run.tsv` |
| N=50 run | `results/budgeted/coarse_to_fine/c2f_single_vector_N50_run.tsv` |
| N=100 run | `results/budgeted/coarse_to_fine/c2f_single_vector_N100_run.tsv` |
| Day 3 summary CSV | `results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.csv` |
| Day 3 summary JSON | `results/budgeted/coarse_to_fine/c2f_single_vector_day3_rerank_summary.json` |

Day 3 的关键发现：

1. Full MV reranker 可以成功在 candidate sets 内运行；
2. rerank run 文件成功生成；
3. reranking 被限制在候选页面内；
4. N=20、50、100 实际候选数仍然没有超过 10；
5. 这进一步确认了 coarse run 深度不足的问题。

Day 3 结论：

> C2F second-stage reranking pipeline 已经跑通，但当前候选集深度限制导致不同 N 的实验条件实际上相同。

---

### 3.4 Day 4：Effect–Latency Evaluation

Day 4 对 C2F N=10、20、50、100 进行了正式评测，并与 Full MV baseline 对照。

核心结果如下：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency | Actual Candidates / Query |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full Multi-vector | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 | - | full corpus |
| C2F N=10 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 10.814267 ms/query | 10.0000 |
| C2F N=20 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 8.275533 ms/query | 10.0000 |
| C2F N=50 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 7.613867 ms/query | 10.0000 |
| C2F N=100 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 7.747500 ms/query | 10.0000 |

关键观察：

1. C2F Recall@10 为 0.2500，高于当前 Full MV baseline 的 0.1333；
2. C2F nDCG@10 为 0.1033，高于 Full MV baseline 的 0.0807；
3. C2F MRR@10 为 0.0628，与 Full MV 的 0.0644 接近；
4. C2F Recall@5 低于 Full MV，说明 early precision 仍然较弱；
5. C2F N=10、20、50、100 的指标完全一致；
6. 所有 N 的 actual candidates/query 都是 10；
7. rerank latency 约为 7.6–10.8 ms/query。

Day 4 结论：

> C2F pipeline 已经完成效果–时延闭环评测。当前 C2F Recall@10 接近 coarse recall 上限，说明主要质量损失发生在 coarse stage。

---

### 3.5 Day 5：Quality–Cost Curve and Best N

Day 5 将 Day 4 的结果转化为第一版 quality-cost curve，并分析 best N。

生成图文件包括：

| 图 | 路径 |
|---|---|
| Recall@10 quality-cost | `results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_Recall10_fixed.png` |
| nDCG@10 quality-cost | `results/budgeted/coarse_to_fine/summary/figures/day5_quality_rerank_cost_nDCG10_fixed.png` |
| Recall@10 quality-latency | `results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_Recall10_fixed.png` |
| nDCG@10 quality-latency | `results/budgeted/coarse_to_fine/summary/figures/day5_quality_latency_nDCG10_fixed.png` |
| Combined quality-cost | `results/budgeted/coarse_to_fine/summary/figures/day5_quality_cost_curve_combined_fixed.png` |

Quality-cost data 如下：

| Method | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |
|---|---:|---:|---:|---:|---:|
| Single-vector coarse | coarse | 0.2500 | 0.1041 | - | 0.0000 |
| Full Multi-vector | full | 0.1333 | 0.0807 | - | 101.0000 |
| C2F N=10 | 10 | 0.2500 | 0.1033 | 10.814267 | 10.0000 |
| C2F N=20 | 20 | 0.2500 | 0.1033 | 8.275533 | 10.0000 |
| C2F N=50 | 50 | 0.2500 | 0.1033 | 7.613867 | 10.0000 |
| C2F N=100 | 100 | 0.2500 | 0.1033 | 7.747500 | 10.0000 |

Best N 分析如下：

| Best Type | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |
|---|---:|---:|---:|---:|---:|
| Principled best trade-off | 10 | 0.2500 | 0.1033 | 10.814267 | 10.0000 |
| Lowest measured latency | 50 | 0.2500 | 0.1033 | 7.613867 | 10.0000 |

Day 5 的最终判断：

> 在当前 limited-depth setting 下，N=10 是最合理的临时 best trade-off。N=50 虽然实测 latency 最低，但由于实际候选数仍为 10，因此不能视为真实最佳 N。

---

### 3.6 Day 6：结果整理与失败模式分析

Day 6 的目标是将本周实验从“方法能跑”整理为“论文能写”，完成结果归纳、失败模式分析和 Week 5 过渡。

本周可整理三类典型案例。

#### A. C2F 成功案例

这类 query 满足：

- gold page 已进入 coarse candidates；
- Full MV reranker 将 relevant page 保留在 top-10；
- 最终 C2F Recall@10 命中。

根据 Day 2 和 Day 4 的结果：

- coarse hit queries 为 8；
- C2F Recall@10 为 0.2500；
- 在 30 条 query 中约有 7–8 条最终命中。

这说明：

> 只要 coarse 阶段成功召回 relevant page，Full MV reranker 大多能够在 top-10 中保留它。

#### B. 小 N 失败、大 N 成功案例

理论上，这类案例用于证明：

- 小 N 下 coarse 漏召回；
- 大 N 下 gold page 进入 candidates；
- fine reranker 能恢复正确排序。

但本周实验中没有观察到该类案例。

原因是：

> 当前 N=10、20、50、100 的实际候选集合都只有 10 个页面，因此不存在真正的小 N 与大 N 差异。

这说明当前实验还不能验证 N scaling 效应。

#### C. 即使大 N 仍失败案例

本周观察到大量此类情况：

- 30 条 query 中有 22 条在 coarse stage 未召回 gold page；
- 因为实际 top-100 仍然只有 top-10 深度，所以这些 query 在所有 N 下都失败；
- C2F reranker 无法恢复 coarse stage 已经丢失的 gold page。

可能原因包括：

1. single-vector visual representation 不足；
2. 页面级全局视觉 embedding 无法捕捉局部细节；
3. PCB 页面中关键证据可能只出现在局部 patch/token；
4. query 与页面之间存在跨模态语义 gap；
5. OCR/textual signal 可能比纯视觉 signal 更强；
6. 部分 query 可能需要跨页证据或更细粒度区域匹配；
7. qrels 或 page-level relevance 可能存在一定歧义。

Day 6 的核心判断：

> 当前失败主要不是 fine reranker 失败，而是 coarse retriever 没有给 reranker 足够好的候选页面。

---

## 4. 本周总体结果

本周核心结果汇总如下：

| Method | Recall@10 | MRR@10 | nDCG@10 | Rerank Cost | Actual Candidates / Query |
|---|---:|---:|---:|---:|---:|
| Single-vector coarse | 0.2500 | - | 0.1041 | 0 | 0 |
| Full Multi-vector | 0.1333 | 0.0644 | 0.0807 | 101 | full corpus |
| C2F N=10 | 0.2500 | 0.0628 | 0.1033 | 10 | 10 |
| C2F N=20 | 0.2500 | 0.0628 | 0.1033 | 10 | 10 |
| C2F N=50 | 0.2500 | 0.0628 | 0.1033 | 10 | 10 |
| C2F N=100 | 0.2500 | 0.0628 | 0.1033 | 10 | 10 |

主要结论：

1. C2F pipeline 已完整跑通；
2. C2F 在当前设置下 Recall@10 达到 0.2500；
3. C2F nDCG@10 达到 0.1033；
4. C2F 效果接近 coarse recall 上限；
5. C2F rerank latency 约为 7.6–10.8 ms/query；
6. 不同 N 的结果完全一致；
7. 当前不能形成真实 quality-cost scaling curve；
8. 当前最合理的临时 best N 是 N=10。

---

## 5. 失败模式分析

### 5.1 Coarse Recall Bottleneck

最主要失败模式是 coarse recall 不足。

| 指标 | 数值 |
|---|---:|
| Coarse Recall | 0.2667 |
| C2F Recall@10 | 0.2500 |

C2F final Recall@10 已经接近 coarse recall 上限，说明 reranker 对候选集合内的 relevant page 保留能力尚可。

因此：

> 主要质量损失发生在 coarse retrieval stage。

---

### 5.2 Candidate Depth Ceiling

本周最大实验限制是 coarse run 深度不足。

| N | Actual Candidates / Query |
|---:|---:|
| 10 | 10 |
| 20 | 10 |
| 50 | 10 |
| 100 | 10 |

这导致：

- N=20、50、100 没有真正扩大候选集合；
- metrics 完全一致；
- latency 不随 N 增长；
- quality-cost curve 中 C2F 点重合；
- 无法判断真实 best N。

---

### 5.3 Early Precision Weakness

C2F Recall@10 高于 Full MV，但 Recall@5 低于 Full MV。

| Method | Recall@5 | Recall@10 |
|---|---:|---:|
| Full MV | 0.1000 | 0.1333 |
| C2F | 0.0333 | 0.2500 |

这说明：

- C2F 能把 relevant page 放入 top-10；
- 但不一定能稳定排到 top-5 或 top-1；
- fine reranker 的排序能力仍有提升空间；
- 当前 C2F 更偏向 recall preservation，而不是 top-rank precision optimization。

---

### 5.4 Visual-only Coarse Retrieval Limitation

Single-vector visual retrieval 作为 coarse retriever 的 recall 较低，说明单一全局视觉向量可能不足以表达 PCB 页面中的细粒度证据。

可能问题包括：

- 页面布局相似但语义不同；
- 局部器件、表格、管脚说明等细节被全局 embedding 稀释；
- query 往往是文本语义，而页面视觉 embedding 不一定能对齐；
- OCR/textual cues 未被 coarse stage 充分利用。

---

## 6. Best N 结论

当前 best N 的判断必须分成两层。

### 6.1 当前实验条件下的 best N

在当前 limited-depth setting 下：

> N=10 是最合理的临时 best trade-off。

原因：

- N=10、20、50、100 的效果完全相同；
- N=10、20、50、100 的 actual candidates/query 都是 10；
- 名义上 N=10 是最小候选预算；
- 因此 N=10 是当前最保守、最可解释的选择。

### 6.2 真实 best N 仍未确定

当前不能声称真实最佳 N 已确定。

原因：

- top-20、top-50、top-100 candidates 实际没有生效；
- 没有观察到 N 增大后 recall 是否提高；
- 没有观察到 rerank cost 是否随 N 增长；
- 没有形成真实 quality-cost curve。

真实 best N 需要重新生成更深的 coarse run 后再判断。

---

## 7. 对 Week 5 的启示

Week 4 的结果对 Week 5 有直接启发。

### 7.1 Patch/Token Selection 的动机

Full MV 成本来自 page-level 多 token/patch matching。

Week 5 可以研究：

- 是否所有 49 个 visual tokens 都必要；
- 是否可以选择 top-k visual patches；
- 是否可以根据 query 动态选择 relevant patches；
- 是否可以压缩 page token 数量以降低 late interaction 成本；
- 是否能在保持效果的同时减少 token-level matching。

### 7.2 Coarse Retriever 改进方向

当前 coarse recall 只有 0.2667，因此 Week 5 也应考虑更强 coarse stage：

1. BM25 coarse retriever；
2. OCR + visual hybrid retriever；
3. single-vector + BM25 fusion；
4. query-type-aware retriever selection；
5. page-level metadata filtering；
6. layout-aware coarse retrieval。

---

## 8. Week 4 总结

Week 4 已成功完成 coarse-to-fine retrieval pipeline 的设计、实现、评测和可视化。

本周最重要的结论是：

> C2F pipeline 已经跑通，并在 cached top-10 candidates setting 下以约 7.6–10.8 ms/query 的 reranking latency 达到 Recall@10 = 0.2500 和 nDCG@10 = 0.1033。然而，由于当前 coarse run 只有 top-10 深度，N=20、50、100 未能真正扩大候选集合，因此本周结果主要证明 pipeline feasibility，而不是最终 quality-cost scaling。

Week 4 为后续工作提供了两个明确方向：

1. 需要更强或更深的 coarse retrieval；
2. 需要研究 patch/token selection 来降低 Full MV late interaction 成本。
