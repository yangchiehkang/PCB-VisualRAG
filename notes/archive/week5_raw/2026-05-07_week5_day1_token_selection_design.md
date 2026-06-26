# Week 5 Day 1 Token Selection Design Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 5  
**Day:** Day 1  
**Date:** 2026-05-07  
**Experiment Name:** Patch/Token Selection Design for Budgeted Multi-vector Retrieval  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

Week 5 Day 1 的目标是确定 patch/token selection 实验方案，明确在每页 multi-vector 表征中“保留哪些 token、丢弃哪些 token”，并固定本周的 M 配置、baseline 对照关系和 token selection 插入位置。

本周整体目标是：

> 在每页只保留部分高价值 patch/token 向量的情况下，显著降低索引体积、matching cost 和 reranking latency，同时尽可能保留检索效果。

Week 4 的 coarse-to-fine 实验主要控制 page-level budget，即减少需要 Full MV reranking 的页面数量。Week 5 进一步控制 token-level budget，即减少每个页面内部参与 late interaction 的 token 数量。

因此，Week 5 的核心框架是：

> Page Budget N + Token Budget M

其中：

- N 控制参与 reranking 的 candidate pages 数量；
- M 控制每个 candidate page 内保留的 token 数量。

---

## 2. 实验背景

Week 3 已经实现 Full Multi-vector Retrieval。每个页面由多个 visual tokens 表示，并通过 late interaction 与 query token embeddings 进行匹配。

Week 4 已经实现 coarse-to-fine retrieval pipeline。该 pipeline 先使用 single-vector visual retrieval 召回 candidate pages，再在候选集合内执行 Full MV reranking。

Week 4 的结果显示：

| Method | Recall@10 | nDCG@10 | Actual Candidates / Query |
|---|---:|---:|---:|
| C2F N=10 | 0.2500 | 0.1033 | 10.0000 |
| C2F N=20 | 0.2500 | 0.1033 | 10.0000 |
| C2F N=50 | 0.2500 | 0.1033 | 10.0000 |
| C2F N=100 | 0.2500 | 0.1033 | 10.0000 |

由于当前 coarse run 实际只提供 top-10 candidates，因此 Week 4 中不同 N 的实际候选数都为 10。

因此，Week 5 固定当前最稳定的 page budget：

> N = 10

在此基础上，只改变每个页面保留的 token 数 M，观察 token budget 对 retrieval quality、index size 和 reranking latency 的影响。

---

## 3. 原始 Token 数确认

根据 Week 3 / Week 4 日志，当前 page multi-vector embedding 的 shape 为：

```text
(49, 512)
```

因此每页原始 visual token 数为：

$$L = 49$$

原计划中的 M 配置为：

$$M \in \{16, 32, 64, 128\}$$

但在当前实验设置下，$$M=64$$ 和 $$M=128$$ 已经超过原始 token 数 $$L=49$$，无法形成真实 token compression。

因此，Week 5 实际采用适配当前数据的 M 配置。

---

## 4. M 配置表

本周固定测试以下 token budget：

| Setting | Kept Tokens M | Original Tokens L | Keep Ratio | Reduction Ratio |
|---|---:|---:|---:|---:|
| M8 | 8 | 49 | 0.1633 | 0.8367 |
| M16 | 16 | 49 | 0.3265 | 0.6735 |
| M24 | 24 | 49 | 0.4898 | 0.5102 |
| M32 | 32 | 49 | 0.6531 | 0.3469 |
| Full / M49 | 49 | 49 | 1.0000 | 0.0000 |

其中 keep ratio 定义为：

$$r = \frac{M}{L}$$

reduction ratio 定义为：

$$1 - r = 1 - \frac{M}{L}$$

该配置覆盖了从极强压缩到接近 Full MV 的多个预算点：

- M8：极强压缩点；
- M16：轻量配置；
- M24：中等配置；
- M32：高质量压缩点；
- M49：Full token setting。

---

## 5. Token Selection 策略

### 5.1 主策略：Norm-based Top-M Token Selection

本周 Day 1 确定的主策略是：

> 根据每个 page token embedding 的 L2 norm 对 tokens 排序，保留 norm 最大的 top-M tokens。

设页面的 full multi-vector 表示为：

$$P = \{v_1, v_2, \dots, v_L\}$$

其中：

- $$L$$ 表示页面原始 token 数；
- $$v_i$$ 表示第 $$i$$ 个 page token embedding。

对每个 token 计算信息量分数：

$$s_i = \|v_i\|_2$$

然后选择分数最高的 M 个 token：

$$P_M = \text{TopM}(P, s_i, M)$$

其中：

$$|P_M| = M$$

后续 Full MV late interaction reranking 只在压缩后的页面表示 $$P_M$$ 上执行：

$$Score(q, p) = \text{LateInteraction}(Q, P_M)$$

---

### 5.2 选择该策略的原因

选择 norm-based token selection 的原因如下：

1. **简单可复现**  
   不需要训练额外模型，也不依赖复杂超参数。

2. **query-independent**  
   可以提前为每个页面生成固定的 compressed page embeddings。

3. **便于统计索引大小**  
   每页固定保留 M 个 tokens，便于计算 index size reduction。

4. **便于与 Full MV 对比**  
   M49 可以作为 full-token 上限，M8/M16/M24/M32 可以形成 budget curve。

5. **适合作为第一版 token selection baseline**  
   在证明 token redundancy 是否存在时，简单策略更容易解释。

---

### 5.3 暂不采用的策略

Day 1 暂不采用以下策略作为主实验：

| 策略 | 暂不采用原因 |
|---|---|
| Query-aware response selection | 依赖 query，难以提前生成静态压缩索引 |
| Learned token selector | 需要训练数据和额外模型，不适合第一版验证 |
| Layout-aware region prior | 需要页面区域标注或额外 layout parser |
| OCR-region prior | 需要 OCR 区域对齐，工程复杂度较高 |

这些方法可以作为后续扩展方向。

---

## 6. Baseline 对照关系

本周实验主要比较以下方法：

| Method | 说明 |
|---|---|
| Full Multi-vector | Week 3 full multi-vector baseline |
| C2F N=10 | Week 4 最稳定的 coarse-to-fine baseline |
| C2F N=10 + M8 | 固定候选页面数，极强 token 压缩 |
| C2F N=10 + M16 | 固定候选页面数，轻量 token budget |
| C2F N=10 + M24 | 固定候选页面数，中等 token budget |
| C2F N=10 + M32 | 固定候选页面数，高质量 token budget |
| C2F N=10 + M49 | 不进行 token selection 的 full-token setting |

其中，Week 5 的核心变量是 M，而不是 N。

固定：

$$N = 10$$

改变：

$$M \in \{8, 16, 24, 32, 49\}$$

---

## 7. Token Selection 插入位置

Token selection 插入在 coarse-to-fine pipeline 的 fine rerank 阶段。

完整流程如下：

```text
Query
  ↓
Single-vector Visual Coarse Retriever
  ↓
Top-N Candidate Pages
  ↓
Load Full Multi-vector Page Embeddings
  ↓
Token Selection: keep top-M page tokens
  ↓
Full MV Late Interaction on selected tokens
  ↓
Final Top-k Ranking
  ↓
Evaluation + Cost Analysis
```

具体说明：

- coarse stage 仍然负责选择 candidate pages；
- token selection 不改变 candidate page set；
- token selection 只压缩候选页面内部的 page multi-vector representation；
- fine reranker 使用压缩后的 page embeddings 进行 late interaction scoring。

---

## 8. 文件命名规划

### 8.1 压缩 Page Embedding 目录

| Setting | Path |
|---|---|
| M8 | `artifacts/embeddings/token_selection/pages_M8/` |
| M16 | `artifacts/embeddings/token_selection/pages_M16/` |
| M24 | `artifacts/embeddings/token_selection/pages_M24/` |
| M32 | `artifacts/embeddings/token_selection/pages_M32/` |
| M49 | `artifacts/embeddings/token_selection/pages_M49/` |

### 8.2 Rerank Run 文件

| Setting | Run File |
|---|---|
| C2F N10 M8 | `results/budgeted/token_selection/c2f_N10_M8_run.tsv` |
| C2F N10 M16 | `results/budgeted/token_selection/c2f_N10_M16_run.tsv` |
| C2F N10 M24 | `results/budgeted/token_selection/c2f_N10_M24_run.tsv` |
| C2F N10 M32 | `results/budgeted/token_selection/c2f_N10_M32_run.tsv` |
| C2F N10 M49 | `results/budgeted/token_selection/c2f_N10_M49_run.tsv` |

### 8.3 Summary 文件

| 文件 | 作用 |
|---|---|
| `results/budgeted/token_selection/summary/token_budget_metrics.csv` | 不同 M 的检索效果 |
| `results/budgeted/token_selection/summary/token_budget_latency.csv` | 不同 M 的 rerank latency |
| `results/budgeted/token_selection/summary/token_budget_index_size.csv` | 不同 M 的索引体积统计 |
| `results/budgeted/token_selection/summary/token_budget_summary.csv` | 效果、成本和压缩率总表 |
| `results/budgeted/token_selection/summary/token_budget_summary.xlsx` | Excel 汇总版本 |
| `results/budgeted/token_selection/figures/token_index_size_curve.png` | 索引体积变化曲线 |
| `results/budgeted/token_selection/figures/token_quality_cost_curve.png` | 质量–成本曲线 |

---

## 9. 本周实验记录模板

### 9.1 不同 M 下的检索效果

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Full MV | - | - | - | - | - |
| C2F N10 M49 | - | - | - | - | - |
| C2F N10 M32 | - | - | - | - | - |
| C2F N10 M24 | - | - | - | - | - |
| C2F N10 M16 | - | - | - | - | - |
| C2F N10 M8 | - | - | - | - | - |

---

### 9.2 不同 M 下的成本记录

| Method | Kept Tokens/Page | Keep Ratio | Index Size | Rerank Time | Per-query Latency |
|---|---:|---:|---:|---:|---:|
| Full MV | 49 | 1.0000 | - | - | - |
| C2F N10 M49 | 49 | 1.0000 | - | - | - |
| C2F N10 M32 | 32 | 0.6531 | - | - | - |
| C2F N10 M24 | 24 | 0.4898 | - | - | - |
| C2F N10 M16 | 16 | 0.3265 | - | - | - |
| C2F N10 M8 | 8 | 0.1633 | - | - | - |

---

### 9.3 Token 压缩比例记录

| Setting | Original Tokens/Page | Kept Tokens/Page | Keep Ratio | Reduction Ratio |
|---|---:|---:|---:|---:|
| M49 | 49 | 49 | 1.0000 | 0.0000 |
| M32 | 49 | 32 | 0.6531 | 0.3469 |
| M24 | 49 | 24 | 0.4898 | 0.5102 |
| M16 | 49 | 16 | 0.3265 | 0.6735 |
| M8 | 49 | 8 | 0.1633 | 0.8367 |

---

## 10. Day 1 验收标准

Day 1 结束时，以下内容已经明确：

- [x] token 选择依据：基于 page token embedding 的 L2 norm；
- [x] token selection 策略：Norm-based Top-M Token Selection；
- [x] M 配置：M=8、16、24、32、49；
- [x] 固定 page budget：N=10；
- [x] 对照方法：Full MV、C2F N=10、C2F N=10 + different M；
- [x] token selection 插入位置：coarse-to-fine 的 fine rerank 阶段；
- [x] 文件命名规范已确定；
- [x] 本周实验记录模板已确定。

---

## 11. 今日结论

Week 5 Day 1 已完成 patch/token selection 实验设计。

本周将固定 Week 4 中最稳定的 page budget：

$$N = 10$$

并在 fine reranking 阶段引入 token budget：

$$M \in \{8, 16, 24, 32, 49\}$$

主实验采用简单、可复现的 norm-based token selection 策略。该策略根据每个 page token embedding 的 L2 norm 选择 top-M tokens，从而构建压缩后的 page representation。

Day 1 的核心判断是：

> 在当前 page embedding shape 为 (49, 512) 的条件下，原计划中的 M=64 和 M=128 不适合作为主实验设置。更合理的 token budget 应为 M=8、16、24、32 和 49/full。Week 5 将以 C2F N=10 为固定 page budget，通过改变 M 来评估 token-level compression 对检索质量、索引体积和 reranking latency 的影响。
