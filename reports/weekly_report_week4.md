# Week 4 周报：Coarse-to-Fine Retrieval 实验总结

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Date:** 2026-05-07  
**Report Title:** Coarse-to-Fine Retrieval with Full Multi-vector Reranking  
**Author:** 杨杰康  
**Status:** Completed  

---

## 摘要

本周完成了 PCB 页面级检索任务中的 coarse-to-fine retrieval pipeline 设计、实现、评测与可视化。系统首先使用低成本 single-vector visual retriever 召回候选页面，然后仅在候选集合内执行 Full Multi-vector late interaction reranking，以降低全库 Full MV matching 的计算成本。

本周实验成功跑通了 N=10、20、50、100 四种候选规模下的 C2F pipeline，并完成了 Recall@10、MRR@10、nDCG@10、rerank latency 和 quality-cost curve 的评测。

当前结果显示，C2F 在实际 10 个 candidates/query 的设置下达到 Recall@10 = 0.2500，nDCG@10 = 0.1033，reranking latency 约为 7.6–10.8 ms/query。相比当前检测到的 Full MV baseline，C2F 在 Recall@10 和 nDCG@10 上更高，但这需要谨慎解释，因为当前 C2F 的候选集合来自 single-vector coarse stage，且 N=20、50、100 实际没有扩大候选集合。

本周最重要的发现是：当前主要瓶颈在 coarse retrieval stage，而不是 Full MV reranker。由于 single-vector coarse run 实际只保留了 top-10，导致所有 N 的 actual candidates/query 都为 10，因此本周结果应被视为 pipeline validation，而不是最终 quality-cost scaling experiment。

---

## 1. 本周研究目标

Week 4 的目标是验证 coarse-to-fine retrieval 是否能够在降低 Full MV 计算成本的同时保持合理的检索效果。

核心研究问题包括：

1. Full MV 是否可以从全库检索转化为候选集内 reranking；
2. C2F 在不同候选规模 N 下的 Recall@10 和 nDCG@10 表现如何；
3. 不同 N 下的 rerank latency 和 cost 是否存在明显变化；
4. 是否可以找到最具性价比的 N；
5. 当前质量损失主要发生在 coarse stage 还是 fine reranker stage；
6. 本周结果对 Week 5 的 patch/token selection 有何启示。

---

## 2. 方法概述

本周采用两阶段检索框架。

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

### 2.1 Coarse Stage

Coarse stage 使用 Week 2 已经跑通的 single-vector visual retrieval。

作用是：

- 从全库页面中快速召回 top-N candidates；
- 降低 Full MV 需要处理的页面数量；
- 为后续 reranking 提供候选集合。

### 2.2 Fine Stage

Fine stage 使用 Week 3 已经跑通的 Full Multi-vector Late Interaction reranker。

作用是：

- 在候选集合内加载 query token embeddings 和 page multi-vector embeddings；
- 对候选页面执行 late interaction scoring；
- 输出最终 reranked top-k results。

### 2.3 评测指标

本周使用的检索指标包括：

| 指标 | 含义 |
|---|---|
| Recall@1 | Top-1 中是否召回 relevant page |
| Recall@5 | Top-5 中是否召回 relevant page |
| Recall@10 | Top-10 中是否召回 relevant page |
| MRR@10 | Top-10 内第一个 relevant page 的 reciprocal rank |
| nDCG@10 | 考虑 ranking position 的归一化排序质量 |

成本指标包括：

| 指标 | 含义 |
|---|---|
| Rerank latency | 每 query 平均 reranking 时间 |
| Actual candidates/query | 每 query 实际参与 reranking 的候选页面数 |
| Rerank cost units | 每 query 被 Full MV scoring 的页面数 |

---

## 3. 实验过程总结

### 3.1 Day 1：实验设计

Day 1 完成 coarse-to-fine retrieval 的整体设计。

主要确定：

- Coarse retriever 使用 single-vector visual retrieval；
- Fine reranker 使用 Full MV late interaction；
- 候选规模设为 N=10、20、50、100；
- 评测指标包括 Recall@10、MRR@10、nDCG@10；
- 成本指标包括 latency 和 actual candidates/query。

Day 1 的结论是：

> Full MV 全库检索成本较高，因此需要通过候选页面预算控制，将 Full MV 限制在少量候选页面内执行。

---

### 3.2 Day 2：Coarse Candidate Pipeline

Day 2 生成了 N=10、20、50、100 的 coarse candidate files。

Coarse recall 结果如下：

| Candidate Depth | Evaluated Queries | Hit Queries | Miss Queries | Coarse Recall |
|---|---:|---:|---:|---:|
| Top-10 | 30 | 8 | 22 | 0.2667 |
| Top-20 | 30 | 8 | 22 | 0.2667 |
| Top-50 | 30 | 8 | 22 | 0.2667 |
| Top-100 | 30 | 8 | 22 | 0.2667 |

该结果说明：

- coarse retriever 只能在 30 条 query 中命中 8 条；
- coarse recall 为 0.2667；
- Top-10、20、50、100 的 recall 完全一致；
- 原始 single-vector visual run 很可能只保存了 top-10；
- 后续 C2F 的最终 recall 会受到 coarse recall 上限限制。

---

### 3.3 Day 3：Full MV Candidate Reranking

Day 3 将 Full MV reranker 接入 Day 2 生成的 candidates。

主要输出：

| N | Run File |
|---:|---|
| 10 | `results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv` |
| 20 | `results/budgeted/coarse_to_fine/c2f_single_vector_N20_run.tsv` |
| 50 | `results/budgeted/coarse_to_fine/c2f_single_vector_N50_run.tsv` |
| 100 | `results/budgeted/coarse_to_fine/c2f_single_vector_N100_run.tsv` |

Day 3 验证了：

- Full MV reranker 能够在候选集合内运行；
- reranking 被严格限制在 candidate pages 内；
- query/page embeddings 能够正常加载；
- N=10、20、50、100 的 rerank run 文件均成功生成。

但也发现：

> 所有 N 的实际候选数仍为 10，说明不同 N 并没有真正扩大 candidate set。

---

### 3.4 Day 4：效果与时延评测

Day 4 对 C2F 各 N 的 run 文件进行了正式评测，并与 Full MV baseline 对照。

核心结果如下：

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Latency | Actual Candidates / Query |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full Multi-vector | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 | - | full corpus |
| C2F N=10 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 10.814267 ms/query | 10.0000 |
| C2F N=20 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 8.275533 ms/query | 10.0000 |
| C2F N=50 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 7.613867 ms/query | 10.0000 |
| C2F N=100 | 0.0333 | 0.0333 | 0.2500 | 0.0628 | 0.1033 | 7.747500 ms/query | 10.0000 |

主要发现：

1. C2F Recall@10 为 0.2500，高于当前 Full MV 的 0.1333；
2. C2F nDCG@10 为 0.1033，高于当前 Full MV 的 0.0807；
3. C2F MRR@10 与 Full MV 接近；
4. C2F Recall@5 低于 Full MV，说明 early precision 不稳定；
5. 四个 N 的结果完全一致；
6. 所有 N 的 actual candidates/query 均为 10。

---

### 3.5 Day 5：质量–成本曲线与 Best N

Day 5 将 Day 4 的结果绘制为 quality-cost curve。

曲线数据如下：

| Method | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |
|---|---:|---:|---:|---:|---:|
| Single-vector coarse | coarse | 0.2500 | 0.1041 | - | 0.0000 |
| Full Multi-vector | full | 0.1333 | 0.0807 | - | 101.0000 |
| C2F N=10 | 10 | 0.2500 | 0.1033 | 10.814267 | 10.0000 |
| C2F N=20 | 20 | 0.2500 | 0.1033 | 8.275533 | 10.0000 |
| C2F N=50 | 50 | 0.2500 | 0.1033 | 7.613867 | 10.0000 |
| C2F N=100 | 100 | 0.2500 | 0.1033 | 7.747500 | 10.0000 |

最重要的图为：

`results/budgeted/coarse_to_fine/summary/figures/day5_quality_cost_curve_combined_fixed.png`

该图显示：

- Single-vector coarse 位于低成本区域；
- C2F 位于低 rerank cost 区域；
- Full MV 位于高 rerank cost 区域；
- C2F N=10、20、50、100 在图中重合。

这说明：

> 当前 quality-cost curve 是 pipeline validation figure，而不是最终 budget-scaling curve。

---

## 4. 主要实验结果

### 4.1 Retrieval Quality

整体结果如下：

| Method | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| Full Multi-vector | 0.1333 | 0.0644 | 0.0807 |
| C2F N=10 | 0.2500 | 0.0628 | 0.1033 |
| C2F N=20 | 0.2500 | 0.0628 | 0.1033 |
| C2F N=50 | 0.2500 | 0.0628 | 0.1033 |
| C2F N=100 | 0.2500 | 0.0628 | 0.1033 |

C2F 在 Recall@10 和 nDCG@10 上高于当前 Full MV baseline，但需要谨慎解释。

原因是：

- C2F 依赖 coarse candidate set；
- 当前 C2F 的 N 并不是真实扩展的 N；
- Full MV 与 C2F 的候选范围和失败模式不同；
- 当前结果更适合说明 C2F pipeline 可行，而不是说明 C2F 全面优于 Full MV。

---

### 4.2 Latency and Cost

C2F reranking latency 如下：

| N | Total Candidates | Avg Candidates / Query | Per-query Latency |
|---:|---:|---:|---:|
| 10 | 300 | 10.0000 | 10.814267 ms |
| 20 | 300 | 10.0000 | 8.275533 ms |
| 50 | 300 | 10.0000 | 7.613867 ms |
| 100 | 300 | 10.0000 | 7.747500 ms |

因为所有 N 实际都 rerank 10 个 candidates，所以 latency 差异不应被解释为 N 的真实影响。

更合理的解释是：

> 当前 reranking latency 约为 7.6–10.8 ms/query，差异主要来自运行波动、缓存状态和系统状态。

---

## 5. Best N 分析

当前 best N 可以从两个角度看。

| Criterion | Selected N | Reason |
|---|---:|---|
| 原则性 best trade-off | 10 | 相同效果、相同实际成本下，N=10 是最小名义预算 |
| 最低实测 latency | 50 | latency 最低，但不是可靠的真实 N 效应 |

最终采用的判断是：

> 在当前 limited-depth coarse run 下，N=10 是最合理的临时 best trade-off。

但真实 best N 仍未确定，因为：

- N=20、50、100 没有真正扩大候选集合；
- 没有观察到 recall 随 N 增长的趋势；
- 没有观察到 rerank cost 随 N 增长的趋势；
- 没有形成真实 quality-cost curve。

---

## 6. 失败模式分析

### 6.1 类型 A：C2F 成功案例

这类案例说明：

- coarse 阶段已经成功召回 relevant page；
- fine 阶段将 relevant page 保留在 top-10；
- 候选集较小但最终效果较好。

本周结果显示：

- coarse hit queries 为 8；
- C2F Recall@10 为 0.2500；
- C2F final Recall@10 接近 coarse recall 上限。

因此可判断：

> 一旦 relevant page 进入候选集合，Full MV reranker 大多能够将其保留在最终 top-10 中。

---

### 6.2 类型 B：小 N 失败、大 N 成功案例

该类案例本周没有被有效观察到。

原因是：

- N=10、20、50、100 的 actual candidates/query 都是 10；
- 大 N 并没有真正扩大 candidate set；
- 因此不存在真实的小 N 与大 N 对比。

这说明：

> 当前实验无法验证“增大 N 是否能恢复 coarse 漏召回”的问题。

---

### 6.3 类型 C：即使大 N 仍失败案例

这是本周最主要的失败模式。

证据：

- 30 条 query 中有 22 条在 coarse stage 未召回 gold page；
- 这些 query 在所有 N 下都失败；
- C2F reranker 无法恢复 coarse 阶段已经丢失的相关页面。

可能原因包括：

1. single-vector visual retriever 召回能力不足；
2. 页面级全局视觉 embedding 无法表达局部细节；
3. query 与页面视觉特征之间存在语义 gap；
4. PCB 页面中的关键证据可能依赖 OCR/text signal；
5. 局部 patch/token 信息可能被全局向量稀释；
6. 部分 query 可能需要跨页或局部区域证据；
7. qrels 或页面级 relevance 可能存在一定歧义。

---

## 7. 对 Week 5 的启示

Week 4 的结果对 Week 5 有两个直接启示。

### 7.1 需要更强或更深的 coarse retrieval

当前 coarse recall 只有 0.2667，是 C2F 的主要瓶颈。

Week 5 可以考虑：

- 重新生成 top-100 或更深的 single-vector visual run；
- 使用 BM25 作为 coarse retriever；
- 使用 OCR + visual hybrid retrieval；
- 使用 BM25 与 visual retrieval score fusion；
- 先评估 coarse recall，再执行 reranking；
- 按 query type 选择不同 coarse retriever。

### 7.2 需要研究 patch/token selection

Full MV 的成本主要来自 token/patch-level matching。

Week 5 可以研究：

- 是否所有 49 个 visual tokens 都必要；
- 是否可以只选择 top-k visual patches；
- 是否可以根据 query 动态选择相关 patch；
- 是否可以降低 late interaction 的 token 数量；
- 是否能在降低成本的同时保持 Recall@10 和 nDCG@10。

---

## 8. 本周结论

Week 4 成功完成了 coarse-to-fine retrieval pipeline 的设计、实现、评测和可视化。

本周关键结论如下：

1. C2F pipeline 已经完整跑通；
2. Full MV reranker 可以在 candidate set 内运行；
3. C2F 在当前设置下达到 Recall@10 = 0.2500；
4. C2F 在当前设置下达到 nDCG@10 = 0.1033；
5. C2F reranking latency 约为 7.6–10.8 ms/query；
6. 当前所有 N 的 actual candidates/query 都是 10；
7. 因此当前结果是 pipeline validation，而不是最终 budget scaling；
8. 当前最合理的临时 best N 是 N=10；
9. 主要质量损失发生在 coarse retrieval stage；
10. Week 5 应重点推进更强 coarse retrieval 和 patch/token selection。

最终判断：

> Week 4 证明了 coarse-to-fine retrieval 在工程上可行，并初步展示了其质量–成本分析流程。但由于当前 coarse candidate depth 不足，真实的 best N 和完整 quality-cost curve 仍需在 Week 5 或后续实验中通过更深的候选集合重新验证。
