powershell -NoProfile -ExecutionPolicy Bypass -Command "@'
# Week 4 Day 1 Coarse-to-Fine Design Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 4  
**Day:** Day 1  
**Date:** 2026-05-07  
**Experiment Name:** Coarse-to-Fine Retrieval Design  
**Author:** 杨杰康  
**Status:** Completed  

---

## 1. 今日目标

今日目标是搭建 Week 4 coarse-to-fine 两阶段检索实验的整体设计框架，明确 coarse 阶段、fine 阶段、候选规模、输入输出文件、成本记录指标和本周实验验收标准。

本周实验的核心思想是：

> 先使用低成本 coarse retriever 从全库中召回有限数量的候选页面，再仅在这些候选页面上执行 Full Multi-vector late interaction reranking，从而降低全量 multi-vector matching 的计算成本。

今日重点不是立即运行正式实验，而是明确两阶段检索系统的设计边界和实验记录规范，为 Day 2 至 Day 5 的实现、评测和成本分析提供统一依据。

---

## 2. 背景与动机

Week 2 的 baseline 实验表明，OCR-based text retrieval 仍然是当前 PCB 页面级检索任务中的强基线。其中 OCR + BM25 取得了当前最强 standalone performance。

Week 3 的 Full Multi-vector Retrieval 实验表明，multi-vector late interaction 相比 single-vector visual retrieval 有明显提升，但成本显著增加。

| Method | Vectors/Page | Vector Dim | Estimated Index Size | Avg Query Latency |
|---|---:|---:|---:|---:|
| Single-vector | 1 | 512 | 0.1973 MB | 0.1130 ms |
| Full Multi-vector | 49 | 512 | 9.6660 MB | 6.5679 ms |

Full Multi-vector 相比 Single-vector 的成本增长为：

| 成本项 | 增长倍数 |
|---|---:|
| Vectors/Page | 49.0x |
| Index Size | 49.0x |
| Avg Query Latency | 58.1x |

因此，Week 4 的研究重点从“Full MV 是否能跑通”转向：

> 如何通过候选页面预算控制，让 Full MV 只作用于少量候选页面，从而形成质量与成本之间的可控折中。

---

## 3. 今日确定的两阶段检索流程

本周固定采用如下 coarse-to-fine 两阶段检索流程：

1. 使用低成本 coarse retriever 从全库召回 top-N 页面；
2. 对 top-N 候选页面执行 Full Multi-vector late interaction reranking；
3. 输出最终 top-k 排序结果；
4. 使用统一 evaluation 脚本评测 page-level retrieval 指标；
5. 记录 coarse time、rerank time、total latency 和 per-query latency；
6. 与 Week 3 的 Full MV 全量检索结果进行对照。

整体流程如下：

    Query
      ↓
    Coarse Retriever
      ↓
    Top-N Candidate Pages
      ↓
    Full Multi-vector Late Interaction Reranker
      ↓
    Final Top-k Ranking
      ↓
    Evaluation + Cost Analysis

---

## 4. Coarse Retriever 选择

### 4.1 今日确定的 coarse retriever

本周 Day 1 按实验计划，优先采用 Week 2 已经跑通的 **Single-vector Visual Retrieval** 作为 coarse retriever。

选择该方法的原因如下：

- 已经有稳定实现；
- 已经有 baseline run 和 metrics；
- 与 Week 3 的 Full MV 视觉 reranker 属于同一视觉检索主线；
- 可以形成清晰的 single-vector coarse retrieval 到 multi-vector fine reranking 的两阶段框架；
- 有助于分析 coarse 阶段召回能力对最终 reranking 结果的影响。

对应已有结果文件为：

| 文件 | 路径 |
|---|---|
| Single-vector visual run | `results/baselines/single_vector_visual_run.tsv` |
| Single-vector visual metrics | `results/baselines/single_vector_visual_metrics.json` |

### 4.2 Coarse retriever 角色定位

Single-vector Visual 在 Week 2 中整体表现较弱，因此本周需要重点检查：

- 它在不同 N 下能否召回 gold page；
- 如果 coarse 阶段漏召回，fine reranker 无法恢复；
- 最终 C2F 结果上限会受到 coarse recall 限制；
- 若 single-vector coarse 效果不足，后续可引入 BM25 coarse 作为更强对照。

Day 1 当前主线固定为：

> Single-vector Visual as Coarse Retriever + Full MV as Fine Reranker

---

## 5. Fine Reranker 设计

Fine 阶段使用 Week 3 已经跑通的 Full Multi-vector Late Interaction Retrieval。

### 5.1 Fine reranker 输入

| 输入 | 路径 |
|---|---|
| Candidate pages | `artifacts/rerank_cache/single_vector_topN/` |
| Query embeddings | `artifacts/embeddings/full_multivector/queries/*.npy` |
| Page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |
| Qrels | `data/metadata/qrels.tsv` |
| Queries | `data/metadata/queries.jsonl` |

### 5.2 Fine reranker scoring

Fine 阶段沿用 Week 3 的 sum-maxsim late interaction scoring：

$$Score(q, d) = \sum_{i=1}^{|Q|} \max_{j=1}^{|D|} sim(q_i, d_j)$$

其中：

- $$q_i$$ 表示 query 的第 $$i$$ 个 token embedding；
- $$d_j$$ 表示页面的第 $$j$$ 个 visual token embedding；
- $$sim(q_i, d_j)$$ 表示 token-level 相似度。

### 5.3 Fine reranker 输出

每个 N 独立输出一个 run 文件：

| Candidate Size | Run 文件 |
|---:|---|
| 10 | `results/budgeted/coarse_to_fine/c2f_single_vector_N10_run.tsv` |
| 20 | `results/budgeted/coarse_to_fine/c2f_single_vector_N20_run.tsv` |
| 50 | `results/budgeted/coarse_to_fine/c2f_single_vector_N50_run.tsv` |
| 100 | `results/budgeted/coarse_to_fine/c2f_single_vector_N100_run.tsv` |

对应 metrics 文件：

| Candidate Size | Metrics 文件 |
|---:|---|
| 10 | `results/budgeted/coarse_to_fine/c2f_single_vector_N10_metrics.json` |
| 20 | `results/budgeted/coarse_to_fine/c2f_single_vector_N20_metrics.json` |
| 50 | `results/budgeted/coarse_to_fine/c2f_single_vector_N50_metrics.json` |
| 100 | `results/budgeted/coarse_to_fine/c2f_single_vector_N100_metrics.json` |

---

## 6. 候选规模设置

今日固定本周主要候选规模为：

| N | 说明 |
|---:|---|
| 10 | 极低候选预算，观察最小 rerank 成本 |
| 20 | 小候选预算，观察是否已接近 Full MV |
| 50 | 中等候选预算，推荐作为主实验设置 |
| 100 | 接近全量页面规模，用于观察上限表现 |

当前页面库规模为 101 页，因此：

- N=100 基本接近全量 Full MV；
- N=50 用于观察是否可在约一半候选规模下保留主要效果；
- N=10 和 N=20 用于观察低成本设置下的性能损失。

---

## 7. 成本记录指标

每个 N 都需要记录效果指标和成本指标。

### 7.1 效果指标

主评测粒度为 page-level retrieval。

| 指标 | 说明 |
|---|---|
| Recall@1 | Top-1 是否命中相关页面 |
| Recall@5 | Top-5 是否命中相关页面 |
| Recall@10 | Top-10 是否命中相关页面 |
| MRR@10 | Top-10 内第一个相关页面的倒数排名均值 |
| nDCG@10 | Top-10 排序质量 |

### 7.2 成本指标

| 指标 | 说明 |
|---|---|
| Coarse Time | coarse retrieval 阶段耗时 |
| Rerank Time | Full MV late interaction reranking 耗时 |
| Total Latency | coarse + rerank 总耗时 |
| Per-query Latency | 平均每条 query 耗时 |
| Candidate Size N | coarse 输出候选数量 |
| Actual Rerank Size | 实际进入 rerank 的候选数量 |
| Avg Rerank Time / Query | 每条 query 平均 rerank 耗时 |
| Memory / GPU Memory | 若方便则记录内存或显存占用 |

### 7.3 Coarse Recall 指标

由于 fine reranker 只能重排候选集合，coarse 阶段召回率决定两阶段系统上限。

需要记录：

| Coarse Recall | 说明 |
|---|---|
| Coarse Recall@10 | gold page 是否进入 coarse top-10 |
| Coarse Recall@20 | gold page 是否进入 coarse top-20 |
| Coarse Recall@50 | gold page 是否进入 coarse top-50 |
| Coarse Recall@100 | gold page 是否进入 coarse top-100 |

---

## 8. 本周计划输出目录

### 8.1 Candidate cache

| 目录 | 用途 |
|---|---|
| `artifacts/rerank_cache/single_vector_topN/` | 保存 single-vector coarse candidates |

候选文件计划命名：

| 文件 | 说明 |
|---|---|
| `single_vector_candidates_top10.tsv` | Top-10 candidates |
| `single_vector_candidates_top20.tsv` | Top-20 candidates |
| `single_vector_candidates_top50.tsv` | Top-50 candidates |
| `single_vector_candidates_top100.tsv` | Top-100 candidates |
| `single_vector_candidates_all.tsv` | 合并候选文件 |

候选文件字段如下：

| 字段 | 说明 |
|---|---|
| `query_id` | 查询编号 |
| `candidate_page_id` | 候选页面编号 |
| `coarse_rank` | coarse 阶段排名 |
| `coarse_score` | coarse 阶段得分 |

### 8.2 Coarse-to-fine results

| 目录 | 用途 |
|---|---|
| `results/budgeted/coarse_to_fine/` | 保存 C2F run、metrics、summary 和 latency |

计划输出文件：

| 文件 | 说明 |
|---|---|
| `c2f_single_vector_N10_run.tsv` | N=10 rerank run |
| `c2f_single_vector_N20_run.tsv` | N=20 rerank run |
| `c2f_single_vector_N50_run.tsv` | N=50 rerank run |
| `c2f_single_vector_N100_run.tsv` | N=100 rerank run |
| `c2f_single_vector_N10_metrics.json` | N=10 metrics |
| `c2f_single_vector_N20_metrics.json` | N=20 metrics |
| `c2f_single_vector_N50_metrics.json` | N=50 metrics |
| `c2f_single_vector_N100_metrics.json` | N=100 metrics |
| `c2f_single_vector_summary.csv` | 不同 N 的效果汇总 |
| `c2f_single_vector_latency.csv` | 不同 N 的时延汇总 |
| `c2f_single_vector_quality_cost.csv` | 质量-成本曲线数据 |

---

## 9. 本周主要对照基线

Week 4 C2F 结果需要与以下方法对照：

| Method | Run 文件 | Metrics 文件 |
|---|---|---|
| Single-vector Visual | `results/baselines/single_vector_visual_run.tsv` | `results/baselines/single_vector_visual_metrics.json` |
| Projected Single-vector | `results/single_vector/single_vector_run.tsv` | `results/single_vector/single_vector_metrics.json` |
| Full Multi-vector | `results/full_multivector/full_mv_run.tsv` | `results/full_multivector/full_mv_metrics.json` |
| OCR + BM25 | `results/baselines/bm25_run.tsv` | `results/baselines/bm25_metrics.json` |

主对照是：

> C2F with single-vector coarse + Full MV rerank vs Full MV full retrieval

辅助对照是：

> C2F vs Single-vector Visual  
> C2F vs OCR + BM25

---

## 10. Day 1 验收清单

| 验收项 | 状态 |
|---|---|
| Coarse 阶段方法已确定 | Completed |
| Fine 阶段方法已确定 | Completed |
| 候选规模 N 已确定 | Completed |
| 成本记录指标已确定 | Completed |
| 输出目录已规划 | Completed |
| Candidate 文件格式已确定 | Completed |
| Run / metrics 命名规则已确定 | Completed |
| Week 4 实验主线已明确 | Completed |

---

## 11. 今日结论

Day 1 已完成 coarse-to-fine retrieval 的整体设计。

本周将采用：

> Single-vector Visual Retrieval as coarse retriever  
> Full Multi-vector Late Interaction as fine reranker

候选规模固定为：

> N = 10, 20, 50, 100

本周实验的主要目标是比较不同候选预算下的 retrieval quality 和 latency cost，判断 coarse-to-fine 是否能够在显著降低 reranking 成本的同时保留 Full MV 的主要检索效果。

今日形成的核心判断是：

> Coarse-to-fine retrieval 是 Week 3 Full MV 成本问题的自然延伸。它通过减少需要执行 expensive late interaction 的页面数量，将 Full MV 从全库检索转化为可预算、可调节、可分析的两阶段检索框架。

---

## 12. 下一步执行入口

Day 2 将开始实现 coarse candidate pipeline。

Day 2 的直接任务是：

- 从 `results/baselines/single_vector_visual_run.tsv` 中读取 coarse ranking；
- 为每个 query 截取 top-10、top-20、top-50、top-100 candidates；
- 输出标准候选文件；
- 统计 coarse Recall@N；
- 记录 coarse 阶段漏召回 query。

Day 2 预期输出：

| 文件 | 说明 |
|---|---|
| `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top10.tsv` | top-10 candidates |
| `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top20.tsv` | top-20 candidates |
| `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top50.tsv` | top-50 candidates |
| `artifacts/rerank_cache/single_vector_topN/single_vector_candidates_top100.tsv` | top-100 candidates |
| `results/budgeted/coarse_to_fine/single_vector_coarse_recall.csv` | coarse recall summary |
'@ | Set-Content -Encoding UTF8 'notes\archive\week4_raw\2026-05-07_week4_day1_coarse_to_fine_design.md'"
