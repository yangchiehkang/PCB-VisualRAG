# Week 3 Weekly Report

**Project:** PCB_VisualRAG_Project  
**Week:** Week 3  
**Date:** 2026-04-04  
**Author:** 杨杰康  
**Student ID:** 225010280  

---

## 1. 本周总体情况

本周的核心目标是将项目从 Week 2 的基础 baseline 对比，推进到论文核心实验方向：**Full Multi-vector Late Interaction Retrieval** 的实现、运行与初步分析。

与 Week 2 不同，本周的重点不再是继续扩展 OCR-based 或 single-vector baseline，而是围绕“建立一个完整、可靠、可评测的 Full Multi-vector 强视觉检索基线”展开。具体来说，本周完成了页面侧多向量 embedding 构建、query token-level embedding 提取、late interaction scoring、小规模闭环验证、正式实验运行、与 single-vector baseline 的系统对比，以及性能—代价分析。

按照第三周预设任务规划，本周核心目标包括：

1. 跑通 Full Multi-vector Retrieval 从 query 到 ranking output 再到 evaluation 的完整实验闭环；
2. 在相同 query、page 库和 qrels 设置下，与 Single-vector 方法形成第一版系统对比；
3. 明确记录 multi-vector 方法带来的性能提升与成本增长，为后续 budgeted multi-vector retrieval 建立实验动机。

截至本周结束，项目已经成功完成 Full Multi-vector 页面侧 embedding 库构建、query projected token embedding 提取、late interaction retrieval 跑通、正式实验运行、与 single-vector baseline 的结果比较，以及性能—代价分析。

整体来看，项目已经从“具备基础 baseline 的页面检索系统”进一步发展为“具备视觉 late interaction 强基线、可进行性能上界与成本边界分析的实验系统”。

本周关键词是：

> 局部匹配、Late Interaction、强视觉基线、性能—代价权衡、Budgeted Retrieval 动机。

---

## 2. 本周完成内容

### 2.1 完成 Full Multi-vector 实验方案设计与小规模子集准备

本周首先明确了 Full Multi-vector Retrieval 的基本实验设计，并准备了小规模验证子集，用于在正式全量运行前验证输入输出、scoring 逻辑和 evaluation 链路。

本阶段主要完成以下工作：

- 明确页面侧采用页面图像的局部视觉 token embeddings；
- 明确 query 侧采用 token-level text embeddings；
- 明确 late interaction scoring 采用 sum-maxsim；
- 构建 small subset，用于优先验证实验链路；
- 准备 Full MV 配置文件、设计说明和实验记录模板。

Full Multi-vector 的基本 scoring 方式为：

$$Score(q, d) = \sum_{i=1}^{|Q|} \max_{j=1}^{|D|} sim(q_i, d_j)$$

其中：

- $$q_i$$ 表示 query 的第 $$i$$ 个 token embedding；
- $$d_j$$ 表示页面的第 $$j$$ 个 visual token embedding；
- $$sim(q_i, d_j)$$ 表示二者之间的相似度。

该 scoring 机制的核心思想是：页面相关性不再由整页全局向量决定，而是由 query token 与页面局部 visual tokens 之间的最佳匹配共同决定。

Small subset 信息如下：

| 项目 | 数量 |
|---|---:|
| Query 数 | 10 |
| Page 数 | 50 |
| 覆盖页面类型 | fabrication、layout、assembly、schematic、bom、other |

相关输出包括：

| 类型 | 路径 |
|---|---|
| Small subset 文件 | `data/metadata/full_mv_small_subset.json` |
| Full MV 设计说明 | `notes/2026-04-09_design_full_multivector.md` |
| Small subset 记录 | `notes/2026-04-09_experiment_full_mv_small_subset.md` |

这一阶段的重要意义在于：它将“Full Multi-vector Retrieval”从抽象方法设想转化为明确可执行的实验对象，并在正式运行前提供了一个规模可控的测试环境。

---

### 2.2 完成页面侧 Full Multi-vector embedding 库构建

在实验设计确定后，本周进入页面侧 multi-vector embedding 提取与存储阶段。

本阶段的目标是：对每个页面图像提取一组局部视觉 token embeddings，并将其以统一格式保存，同时生成 metadata、token 统计信息和运行日志，为后续 retrieval 阶段提供标准化输入。

本阶段使用的模型为：

| 项目 | 设置 |
|---|---|
| Model | `openai/clip-vit-base-patch32` |
| Page representation | Local visual tokens |
| CLS token | 不保留 |
| Token 数 / 页 | 49 |
| 初始 hidden dim | 768 |
| 修正后 projected dim | 512 |
| Normalization | Enabled |
| Page embedding 输出目录 | `artifacts/embeddings/full_multivector/pages/` |

本周最初使用的模型名称为 `clip-vit-base-patch32`，运行时报错。排查后发现该名称不是 Hugging Face 上合法的 repo id，因此修正为：

- `openai/clip-vit-base-patch32`

修正后模型成功加载，页面 embedding 提取脚本正常运行。

---

#### 2.2.1 Small subset 页面 embedding 测试

为了降低调试风险，首先在 small subset 上运行页面 embedding 提取流程。结果如下：

| 项目 | 结果 |
|---|---:|
| 页面总数 | 50 |
| 成功处理 | 50 |
| 失败处理 | 0 |
| 初始 embedding shape | `(49, 768)` |
| 运行耗时 | 约 5.84 秒 |

该结果表明：

- 页面图像路径解析正常；
- 模型加载正常；
- embedding 文件可以正常落盘；
- metadata 与 token 统计文件可以生成；
- 后续可以扩展到全量页面。

---

#### 2.2.2 全量页面 embedding 构建

Small subset 测试成功后，进一步对全量页面库进行 embedding 提取。当前 page inventory 共包含 101 个页面。

全量运行结果如下：

| 项目 | 结果 |
|---|---:|
| 页面总数 | 101 |
| 成功处理页面 | 101 |
| 失败页面 | 0 |
| 每页 token 数 | 49 |
| 初始 embedding shape | `(49, 768)` |
| 修正后 embedding shape | `(49, 512)` |
| 全量运行耗时 | 约 11.30 秒 |

相关输出包括：

| 类型 | 路径 |
|---|---|
| Page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |
| Page meta | `artifacts/embeddings/full_multivector/page_embedding_meta.jsonl` |
| Token stats JSON | `artifacts/embeddings/full_multivector/token_stats.json` |
| Token stats CSV | `artifacts/embeddings/full_multivector/token_stats.csv` |
| Page type stats | `artifacts/embeddings/full_multivector/token_stats_by_page_type.csv` |
| Page embedding log | `artifacts/embeddings/full_multivector/page_embedding_run.log` |

页面侧 multi-vector embedding pipeline 已经能够稳定运行，并形成统一的页面多向量库。

---

### 2.3 完成 query token embedding 与 late interaction 小规模闭环

页面侧 multi-vector 库构建完成后，本周进一步实现 query token embedding 与 late interaction scoring，使 Full Multi-vector Retrieval 真正形成完整检索闭环。

本阶段主要完成以下工作：

- 使用 CLIP text tower 提取 query token embeddings；
- 修正 query/page embedding 维度不一致问题；
- 使用 projected visual tokens 重新生成 page embeddings；
- 实现 sum-maxsim late interaction scoring；
- 在 small subset 上生成 run 文件并完成 evaluation。

---

#### 2.3.1 Query embedding 提取

Query 侧使用 token-level text embeddings，并最终统一到 CLIP projection space。

结果如下：

| 项目 | 结果 |
|---|---:|
| Query 数量 | 30 |
| Query embedding 类型 | Projected text token embeddings |
| Embedding dim | 512 |
| 输出目录 | `artifacts/embeddings/full_multivector/queries/` |

相关输出包括：

| 类型 | 路径 |
|---|---|
| Query embeddings | `artifacts/embeddings/full_multivector/queries/*.npy` |
| Query meta | `artifacts/embeddings/full_multivector/query_embedding_meta.jsonl` |

---

#### 2.3.2 修正 query/page embedding 空间不一致问题

在初始实现中发现 query 和 page embeddings 维度不一致：

| 对象 | 初始维度 |
|---|---|
| Query embeddings | `(n, 512)` |
| Page embeddings | `(49, 768)` |

进一步排查后确认：

- query 侧已经进入 CLIP shared projection space；
- page 侧最初使用的是视觉 tower 输出的原始 hidden states；
- 二者不在同一向量空间中，无法直接进行相似度计算。

因此，对页面表示进行了修正：

- 页面侧改用 `visual_projection` 之后的 projected visual tokens；
- page embeddings 由 `(49, 768)` 修正为 `(49, 512)`；
- query/page embeddings 统一到 512 维共享空间。

修正后：

| 对象 | 最终维度 |
|---|---|
| Query embeddings | `(n, 512)` |
| Page embeddings | `(49, 512)` |

这一修正非常关键，因为它保证了 late interaction scoring 是在同一 embedding space 中进行的。

---

#### 2.3.3 Small subset late interaction 闭环

修正 embedding 空间后，在 small subset 上成功跑通：

> query embedding → late interaction scoring → top-k ranking → evaluation

成功生成：

| 类型 | 路径 |
|---|---|
| Small run | `results/full_multivector/full_mv_small_run.tsv` |
| Small metrics | `results/full_multivector/full_mv_small_metrics.json` |

Small subset page-level 结果如下：

| Metric | Full MV Small |
|---|---:|
| MRR@10 | 0.0272 |
| Recall@1 | 0.0000 |
| Recall@5 | 0.0667 |
| Recall@10 | 0.1667 |
| nDCG@10 | 0.0638 |

Doc-level 辅助结果如下：

| Metric | Full MV Small |
|---|---:|
| Doc Recall@1 | 0.0333 |
| Doc Recall@5 | 0.8000 |
| Doc Recall@10 | 1.0000 |

虽然 small subset 的 page-level 指标仍然不高，但该实验验证了 Full Multi-vector Retrieval 的核心闭环已经跑通。

---

### 2.4 完成 Full Multi-vector 正式实验

在 small subset 成功跑通后，本周进一步将 Full Multi-vector Retrieval 扩展到正式实验规模，即使用全部 query 和全部页面 embedding 进行检索。

正式实验成功生成：

| 类型 | 路径 |
|---|---|
| Full MV run | `results/full_multivector/full_mv_run.tsv` |
| Full MV metrics | `results/full_multivector/full_mv_metrics.json` |

Full Multi-vector 正式实验 page-level 结果如下：

| Metric | Full Multi-vector |
|---|---:|
| MRR@10 | 0.0644 |
| Recall@1 | 0.0333 |
| Recall@5 | 0.1000 |
| Recall@10 | 0.1333 |
| nDCG@10 | 0.0807 |

Doc-level 辅助结果如下：

| Metric | Full Multi-vector |
|---|---:|
| Doc Recall@1 | 0.7333 |
| Doc Recall@5 | 0.9000 |
| Doc Recall@10 | 0.9000 |

从结果看，Full MV 在 doc-level 上具有较强能力，能够较稳定地将相关页面所在文档召回到前列。但在 page-level 精确页面定位上仍然存在明显提升空间。

这说明当前 Full MV 已经具备一定视觉结构感知能力，但还不足以直接作为强 standalone page retriever 替代文本检索方法。

---

### 2.5 完成 Single-vector baseline 构建与系统对比

为了验证 multi-vector late interaction 是否真的优于单向量表示，本周基于同一套 projected embeddings 构建了 Single-vector baseline。

Single-vector 的构建方式如下：

- query token mean pooling；
- page token mean pooling；
- cosine / dot-product 排序；
- 与 Full MV 使用相同 query、page 库和 qrels。

相关输出包括：

| 类型 | 路径 |
|---|---|
| Single-vector run | `results/single_vector/single_vector_run.tsv` |
| Single-vector metrics | `results/single_vector/single_vector_metrics.json` |
| Query-level 对比 | `results/comparisons/full_vs_single_query_level.csv` |

Single-vector page-level 结果如下：

| Metric | Single-vector |
|---|---:|
| MRR@10 | 0.0000 |
| Recall@1 | 0.0000 |
| Recall@5 | 0.0000 |
| Recall@10 | 0.0000 |
| nDCG@10 | 0.0000 |

Single-vector doc-level 辅助结果如下：

| Metric | Single-vector |
|---|---:|
| Doc Recall@1 | 0.0333 |
| Doc Recall@5 | 0.7000 |
| Doc Recall@10 | 0.7333 |

Full MV 与 Single-vector 的 page-level 对比如下：

| Method | MRR@10 | Recall@1 | Recall@5 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Single-vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Full Multi-vector | 0.0644 | 0.0333 | 0.1000 | 0.1333 | 0.0807 |

Doc-level 辅助指标对比如下：

| Method | Doc Recall@1 | Doc Recall@5 | Doc Recall@10 |
|---|---:|---:|---:|
| Single-vector | 0.0333 | 0.7000 | 0.7333 |
| Full Multi-vector | 0.7333 | 0.9000 | 0.9000 |

该结果说明：

> 在当前 PCB 工程文档页面检索任务中，局部 token-level matching 明显优于全局 mean pooling 表示。

Full Multi-vector 不仅在 page-level 上优于 Single-vector，在 doc-level 辅助指标上也表现更强。这说明从全局页面向量过渡到局部 token 匹配，确实能够提升视觉检索能力。

---

### 2.6 完成 Full MV 成本统计与性能—代价分析

在完成正式实验和 baseline 对比后，本周进一步进行了 Full MV 的成本分析，并与 Single-vector 做性能—代价对照。

本阶段主要统计以下成本项：

- vectors per page；
- vector dim；
- estimated raw index size；
- avg query latency；
- late interaction scoring cost。

成本对比如下：

| Method | Vectors/Page | Vector Dim | Estimated Raw Index Size | Avg Query Latency |
|---|---:|---:|---:|---:|
| Single-vector | 1 | 512 | 0.1973 MB | 0.1130 ms |
| Full Multi-vector | 49 | 512 | 9.6660 MB | 6.5679 ms |

Full MV 额外记录：

| Cost Item | Value |
|---|---:|
| Avg late interaction scoring cost | 6.5452 ms |

Full MV 相比 Single-vector 的成本增长为：

| 成本项 | 增长倍数 |
|---|---:|
| Vectors/Page | 49.0x |
| Index Size | 49.0x |
| Avg Query Latency | 58.1x |

性能与成本结合来看，可以得到本周最重要的一条阶段性论证链条：

1. Full MV 在 page-level retrieval 上优于 Single-vector；
2. Full MV 在 doc-level retrieval 上也优于 Single-vector；
3. Full MV 的额外成本主要来自 multi-vector late interaction scoring；
4. Full MV 是“更强但也更贵”的方法；
5. 因此后续研究 budgeted multi-vector retrieval 是合理且必要的。

---

## 3. 本周关键实验结果

### 3.1 Full Multi-vector 与 Single-vector 的正式对比

本周最核心的实验结果是 Full MV 与 Single-vector 的正式对比。

| Method | MRR@10 | Recall@1 | Recall@5 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Single-vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Full Multi-vector | 0.0644 | 0.0333 | 0.1000 | 0.1333 | 0.0807 |

从结果可以看到，Single-vector 在 page-level 上几乎完全失效，而 Full MV 能够取得一定召回和排序效果。

这说明单个全局向量难以表达 PCB 工程文档页面中的细粒度结构、表格、图例和局部标注；而 Full MV 通过保留局部 token 并使用 late interaction matching，能够恢复部分局部结构感知能力。

---

### 3.2 Doc-level 辅助结果

Doc-level 辅助指标如下：

| Method | Doc Recall@1 | Doc Recall@5 | Doc Recall@10 |
|---|---:|---:|---:|
| Single-vector | 0.0333 | 0.7000 | 0.7333 |
| Full Multi-vector | 0.7333 | 0.9000 | 0.9000 |

Doc-level 结果说明，Full MV 能够较稳定地将相关文档召回到前列。这表明视觉 token-level matching 对文档级相关性判断是有效的。

不过，Full MV 在 page-level 上仍然偏低，说明当前系统的主要瓶颈是：

> 能找到相关文档，但还不能稳定定位到文档中的精确目标页面。

---

### 3.3 成本对比结果

Full MV 与 Single-vector 的成本对比如下：

| Method | Vectors/Page | Vector Dim | Estimated Index Size | Avg Query Latency |
|---|---:|---:|---:|---:|
| Single-vector | 1 | 512 | 0.1973 MB | 0.1130 ms |
| Full Multi-vector | 49 | 512 | 9.6660 MB | 6.5679 ms |

这一结果说明 Full MV 当前是一个典型的“更强但更贵”的方案。它适合作为后续预算化方法的性能上限基线，而不是最终部署形态。

---

## 4. 本周实验解读

### 4.1 Full Multi-vector Retrieval 已经成功跑通

本周最关键的成果不是单个指标数值，而是完整建立了 Full Multi-vector Retrieval 实验闭环：

> page multi-vector extraction → query token embedding → late interaction scoring → run output → evaluation → comparison → cost analysis

这意味着 Full MV 已经从理论设想进入“可运行、可评测、可对照”的实验阶段。

---

### 4.2 局部 token matching 优于全局单向量表示

当前 Single-vector 在 page-level 上表现为 0，而 Full MV 已经取得非零召回和排序结果。

这说明在 PCB 工程文档页面检索场景下，全局视觉语义不足以覆盖页面中的：

- 局部结构；
- 表格内容；
- 元件标注；
- 图例区域；
- 版图布局；
- 细粒度视觉证据。

相比之下，multi-vector late interaction 更适合保留页面内部局部区域信息，因此比全局 mean pooling 更适合该任务。

---

### 4.3 Full MV 尚未超过 OCR/Text baseline

虽然 Full MV 明显优于 Single-vector，但与 Week 2 的 OCR + BM25 相比，Full MV 仍然明显偏弱。

Week 2 BM25 结果为：

| Method | Recall@10 | MRR | nDCG@10 |
|---|---:|---:|---:|
| OCR + BM25 | 0.8833 | 0.4105 | 0.5241 |
| Full Multi-vector | 0.1333 | 0.0644 | 0.0807 |

因此，本周实验并不支持“视觉方法已经超过文本检索”的结论。

更合理的判断是：

- OCR/Text 仍然是强 standalone baseline；
- Full MV 是比 Single-vector 更强的视觉检索方法；
- Full MV 当前更适合作为视觉补充信号；
- 后续应优先探索 BM25 + Full MV reranking 或 text-visual fusion。

---

### 4.4 成本上升支撑 Budgeted Retrieval 研究动机

Full MV 的 vectors/page、index size 和 query latency 都出现数十倍增长。这说明直接将 Full MV 作为全量检索器并不理想。

因此，后续研究 budgeted multi-vector retrieval 具有明确动机：

- 如何减少每页保留的 visual tokens；
- 如何只对 top-N candidate pages 做 late interaction；
- 如何在尽量保持检索性能的前提下降低 latency 和 index size；
- 如何构建 performance-cost Pareto curve。

这为后续论文方法部分提供了清晰的研究问题：

> 如何在预算约束下保留 multi-vector late interaction 的局部匹配能力，同时降低存储和检索成本？

---

## 5. 本周新增脚本与结果文件

### 5.1 新增或重点使用脚本

本周新增或重点使用的脚本包括：

| 脚本 | 作用 |
|---|---|
| `scripts/retrieval/run_full_multivector_page_embeddings.py` | 提取页面侧 visual token embeddings |
| `scripts/retrieval/run_full_multivector_query_embeddings.py` | 提取 query token embeddings |
| `scripts/retrieval/run_full_multivector_small_retrieval.py` | 运行 small subset Full MV retrieval |
| `scripts/retrieval/run_full_multivector_retrieval.py` | 运行 full-scale Full MV retrieval |
| `scripts/retrieval/run_single_vector_retrieval.py` | 基于 projected embeddings 构建 Single-vector 对照 |
| `scripts/eval/eval_full_multivector_run.py` | Full MV 结果评测 |
| `scripts/analysis/compare_full_mv_vs_single.py` | Full MV 与 Single-vector 对比 |
| `scripts/analysis/analyze_full_mv_cost.py` | Full MV 成本分析 |
| `scripts/analysis/analyze_single_vector_cost.py` | Single-vector 成本分析 |
| `scripts/analysis/build_perf_cost_comparison.py` | 构建性能—成本对比表 |
| `scripts/analysis/build_perf_cost_comparison_with_ratio.py` | 构建带倍数比例的性能—成本对比表 |

---

### 5.2 关键输入与中间产物

本周形成的关键中间产物包括：

| 文件或目录 | 说明 |
|---|---|
| `artifacts/embeddings/full_multivector/pages/*.npy` | 页面侧 multi-vector embeddings |
| `artifacts/embeddings/full_multivector/queries/*.npy` | Query token embeddings |
| `artifacts/embeddings/full_multivector/page_embedding_meta.jsonl` | 页面 embedding 元信息 |
| `artifacts/embeddings/full_multivector/query_embedding_meta.jsonl` | Query embedding 元信息 |
| `artifacts/embeddings/full_multivector/token_stats.json` | Token 统计 |
| `artifacts/embeddings/full_multivector/token_stats.csv` | Token 统计 CSV |
| `artifacts/embeddings/full_multivector/token_stats_by_page_type.csv` | 按页面类型统计 token 信息 |

---

### 5.3 关键结果文件

本周产生的关键结果文件包括：

| 文件 | 说明 |
|---|---|
| `results/full_multivector/full_mv_small_run.tsv` | Full MV small subset run |
| `results/full_multivector/full_mv_small_metrics.json` | Full MV small subset metrics |
| `results/full_multivector/full_mv_run.tsv` | Full MV 正式检索结果 |
| `results/full_multivector/full_mv_metrics.json` | Full MV 正式指标 |
| `results/single_vector/single_vector_run.tsv` | Single-vector 对照 run |
| `results/single_vector/single_vector_metrics.json` | Single-vector 对照指标 |
| `results/comparisons/full_vs_single_query_level.csv` | Query-level 对比结果 |
| `results/analysis/full_mv_cost_stats.csv` | Full MV 成本统计 |
| `results/analysis/single_vector_cost_stats.csv` | Single-vector 成本统计 |
| `results/analysis/perf_cost_comparison.csv` | 性能—成本对比 |
| `results/analysis/perf_cost_comparison_with_ratio.csv` | 带倍数比例的性能—成本对比 |

这些文件已经构成后续论文中“Full Multi-vector 强视觉基线”和“Budgeted Retrieval 动机”的基础材料。

---

## 6. 当前项目状态

截至 Week 3 结束，项目已经完成以下关键阶段：

- 页面级检索任务定义完成；
- OCR/Text baseline 完成；
- Single-vector Visual baseline 完成；
- Full Multi-vector 页面侧 embedding 构建完成；
- Query token embedding 构建完成；
- Late interaction scoring 实现完成；
- Small subset 闭环跑通；
- Full-scale Full MV 检索完成；
- Full MV 与 Single-vector 系统对比完成；
- Full MV 成本分析完成。

因此，项目当前已经从“基础 baseline 阶段”进入到“多向量视觉检索与预算化优化阶段”。

---

## 7. 当前仍存在的问题

### 7.1 Full MV page-level 指标仍然偏低

Full MV 相比 Single-vector 有明显提升，但 page-level Recall@10 仍只有 0.1333，说明当前视觉方法还不能稳定定位目标页面。

可能原因包括：

- CLIP visual tokens 对工程图纸细节不够敏感；
- query text 与页面 visual token 的跨模态匹配仍较弱；
- 页面内大量文本、表格和符号难以由纯视觉 token 表达；
- 多个相似页面之间的视觉差异较小。

---

### 7.2 Full MV 与 OCR + BM25 仍有明显差距

Week 2 的 OCR + BM25 Recall@10 为 0.8833，而 Full MV Recall@10 为 0.1333。

这说明视觉方法当前不适合作为 OCR/Text 的直接替代品。后续更合理的方向是：

- BM25 top-N + Full MV reranking；
- BM25 score 与 Full MV score fusion；
- OCR text + visual token hybrid retrieval；
- 使用视觉方法增强结构感知和证据归因。

---

### 7.3 Full MV 成本显著增加

Full MV 的向量数量、存储和检索延迟均显著高于 Single-vector：

- vectors/page 增加 49 倍；
- index size 增加 49 倍；
- avg query latency 增加 58.1 倍。

这说明后续必须研究预算化策略，而不是直接将 Full MV 全量部署为最终方案。

---

### 7.4 Evaluation 粒度需要持续保持一致

本周排查发现，如果 qrels 是 page-level，但 evaluation 脚本按 doc-level 做主比较，会导致结果异常。

后续所有实验必须明确：

- page-level 是主评测口径；
- doc-level 只作为辅助指标；
- run 文件中的主键应为 `page_id`；
- qrels 与 run 文件必须保持同一粒度。

---

### 7.5 需要进一步开展 query-level error analysis

目前已经有 overall metrics 和方法对比，但仍需要进一步分析：

- 哪些 query 是 Full MV 明显优于 Single-vector 的；
- 哪些 query Full MV 仍然失败；
- Full MV 是否对某些 query type 更有效；
- Full MV 失败是否来自视觉相似页面干扰；
- BM25 与 Full MV 是否具有互补性。

---

## 8. 下周计划

下周工作重点将从“建立 Full MV 强基线”转向“围绕成本和互补性进行优化设计”。

---

### 8.1 开展 BM25 top-N + Full MV Reranking

基于 Week 2 和 Week 3 结果，最自然的下一步是使用 BM25 作为 coarse retriever，再用 Full MV 对 BM25 top-N 页面进行 reranking。

计划测试候选规模：

| Candidate Size | 目的 |
|---:|---|
| 10 | 极低成本 reranking |
| 20 | 小候选集实验 |
| 50 | 推荐主实验设置 |
| 100 | 接近全量上限 |

重点观察：

- BM25 top-N 是否覆盖 gold pages；
- Full MV reranking 是否提升 MRR；
- Full MV reranking 是否提升 nDCG@10；
- 不同 N 下 latency 如何变化；
- 文本和视觉信号是否互补。

---

### 8.2 开展 Full MV query-level case analysis

计划选取以下几类 query 进行案例分析：

- Full MV 明显优于 Single-vector 的 query；
- Full MV 和 Single-vector 都失败的 query；
- BM25 成功但 Full MV 失败的 query；
- BM25 失败但 Full MV 有补充召回的 query；
- 视觉相似页面导致误检的 query。

该分析将为论文中的 case study 和 error analysis 提供材料。

---

### 8.3 设计 Token Budget 实验

下一阶段将围绕每页保留多少 visual tokens 开展预算化实验。

候选 token budget 包括：

| Token Budget | 含义 |
|---:|---|
| 4 | 极低 token 预算 |
| 8 | 小预算 |
| 16 | 中等预算 |
| 32 | 高预算 |
| 49 | Full MV 上限 |

目标是绘制 performance-cost trade-off 曲线，分析在减少 token 数量时性能下降是否可控。

---

### 8.4 继续完善实验脚本与结果管理

后续需要进一步规范：

- `results/budgeted/` 目录结构；
- rerank cache 存储路径；
- 不同 N、M 设置下的命名规则；
- run / metrics / summary 文件输出格式；
- query-level 分析表生成流程。

建议新增目录包括：

| 目录 | 用途 |
|---|---|
| `results/budgeted/coarse_to_fine/` | BM25 top-N + Full MV reranking |
| `results/budgeted/token_selection/` | Token budget 实验 |
| `results/budgeted/fusion/` | Text-visual score fusion |
| `artifacts/rerank_cache/bm25_topN/` | BM25 候选集缓存 |

---

## 9. 本周总结

Week 3 是项目进入核心实验阶段的关键一周。

本周最大的成果不是某一个指标本身，而是成功建立了 Full Multi-vector Late Interaction Retrieval 的完整实验管线，并在与 Single-vector 的正式对比中初步证明：

1. Full MV 确实比 Single-vector 更强；
2. 局部 token-level matching 对 PCB 工程文档页面检索有价值；
3. Full MV 在 doc-level 上具有较强相关文档定位能力；
4. Full MV 的 page-level 精确定位仍然不足；
5. Full MV 的计算和存储成本显著增加；
6. 后续研究 budgeted multi-vector retrieval 是合理且必要的。

与 Week 2 相比，本周工作让项目从“具备 OCR/Text 与单向量视觉 baseline 的实验系统”，进一步发展为“拥有视觉 late interaction 强基线、可做性能上界与成本边界分析的实验系统”。

当前最稳妥的论文叙事应是：

> OCR/Text retrieval 仍然是 PCB 工程文档检索中的强基线；single-vector visual retrieval 难以表达页面局部结构；Full Multi-vector Late Interaction 能够提升视觉检索能力，但代价显著增加。因此，后续研究重点应转向 BM25-guided reranking、token budget control 和 budgeted multi-vector retrieval，以在性能和成本之间取得更合理的权衡。
