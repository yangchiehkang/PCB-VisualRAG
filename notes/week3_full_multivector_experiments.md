# Week 3 Full Multi-vector Experiments Log

**Project:** PCB_VisualRAG_Project  
**Stage:** Week 3  
**Date Range:** 2026-04-09 to 2026-04-10  
**Topic:** Full Multi-vector Late Interaction Retrieval  
**Status:** Completed  

---

## 1. 本阶段目标

Week 3 的核心目标是建立 Full Multi-vector Late Interaction 检索管线，并验证其相对于 single-vector visual representation 的优势与成本。

本阶段重点完成以下工作：

- 设计 Full Multi-vector Retrieval 方法；
- 构建页面侧 visual token embedding 库；
- 构建 query 侧 token-level embedding 库；
- 实现 late interaction scoring；
- 完成 small subset 闭环测试；
- 完成 full-scale retrieval；
- 与 single-vector baseline 对比；
- 分析 Full MV 的性能与成本。

本阶段核心问题是：

> 对于 PCB 工程文档页面检索，multi-vector late interaction 是否比 single-vector visual retrieval 更适合表达局部结构？它带来的成本是否显著？

---

## 2. 方法设计

### 2.1 页面侧表示

页面侧采用局部视觉 token / patch embeddings 作为多向量表示。

基本设定如下：

| 项目 | 设置 |
|---|---|
| 输入 | `data/images/` 下的页面图像 |
| 模型 | `openai/clip-vit-base-patch32` |
| 页面表示 | Local visual tokens |
| CLS token | 不保留 |
| 每页 token 数 | 49 |
| 原始 visual hidden dim | 768 |
| Projected dim | 512 |
| Normalization | Enabled |
| 输出目录 | `artifacts/embeddings/full_multivector/pages/` |

页面侧每个页面保存为一个 `.npy` 文件，例如：

- `artifacts/embeddings/full_multivector/pages/doc001_p001.npy`
- `artifacts/embeddings/full_multivector/pages/doc003_p010.npy`

最终页面 embedding shape 为：

- `(49, 512)`

---

### 2.2 Query 侧表示

Query 侧采用 token-level text embeddings。

基本设定如下：

| 项目 | 设置 |
|---|---|
| 输入 | `data/metadata/queries.jsonl` |
| 模型 | `openai/clip-vit-base-patch32` |
| 表示 | Projected text token embeddings |
| 最大长度 | 32 |
| 输出目录 | `artifacts/embeddings/full_multivector/queries/` |

每条 query 保存为一个 `.npy` 文件，例如：

- `artifacts/embeddings/full_multivector/queries/q001.npy`
- `artifacts/embeddings/full_multivector/queries/q030.npy`

最终 query embedding dim 为：

- `512`

---

### 2.3 Late Interaction Scoring

Full Multi-vector Retrieval 使用 sum-maxsim 作为 late interaction scoring。

对于 query token 集合和 page token 集合，计算方式为：

- 对每个 query token，找到其与页面所有 visual tokens 中最相似的 token；
- 将所有 query token 的最大相似度求和；
- 得到 query-page relevance score。

该方法的直觉是：

> 页面是否相关，不取决于整页的全局平均表示，而取决于 query 中每个语义 token 是否能在页面局部区域中找到匹配证据。

---

## 3. Day 1：Full MV 设计与 Small Subset 构建

### 3.1 目标

Day 1 的目标是明确 Full Multi-vector 的实验设计，并创建 small subset 进行低风险调试。

---

### 3.2 Small Subset 信息

Small subset 创建时间：

- 2026-04-09 12:48:12

Subset 规模：

| 项目 | 数量 |
|---|---:|
| Queries | 10 |
| Pages | 50 |

相关文件：

| 类型 | 路径 |
|---|---|
| Subset 文件 | `data/metadata/full_mv_small_subset.json` |
| Subset 实验记录 | `notes/2026-04-09_experiment_full_mv_small_subset.md` |

---

### 3.3 Small Subset Queries

Small subset 包含 q001 到 q010，主要覆盖 fabrication table、breakaway/bevel diagram、board outline、drill table、assembly drawing、BOM、schematic、PCB layer stack 等页面检索场景。

这组 subset 的作用是：

- 验证 query/page ID 对齐；
- 验证 embedding 文件生成；
- 验证 late interaction scoring；
- 验证 run 文件输出；
- 验证 evaluation 脚本是否能正确读取结果。

---

## 4. Day 2：页面侧 Multi-vector Embedding 构建

### 4.1 目标

Day 2 的目标是为所有页面构建 multi-vector visual token embedding 库。

---

### 4.2 配置与模型修正

最初模型名称写为：

- `clip-vit-base-patch32`

运行时报错，原因是该名称不是 Hugging Face 的合法 repo id。

随后修正为：

- `openai/clip-vit-base-patch32`

模型成功加载后，页面 embedding 提取流程正常运行。

---

### 4.3 Small Subset 测试结果

Small subset 测试结果如下：

| 项目 | 结果 |
|---|---:|
| 页面数 | 50 |
| 成功处理 | 50 |
| 失败处理 | 0 |
| 初始 embedding shape | `(49, 768)` |
| 运行耗时 | 约 5.84 秒 |

该结果表明：

- 图像路径解析正常；
- 模型加载正常；
- 页面 embedding 文件可正常保存；
- 每页 token 数保持一致；
- 后续可以扩展到全量页面。

---

### 4.4 Full Page Embedding 构建结果

全量页面 embedding 构建结果如下：

| 项目 | 结果 |
|---|---:|
| 页面总数 | 101 |
| 成功处理页面 | 101 |
| 失败页面 | 0 |
| 每页 token 数 | 49 |
| 原始 hidden dim | 768 |
| Projected dim | 512 |
| CLS token | 不保留 |
| Normalization | Enabled |
| 全量耗时 | 约 11.30 秒 |

输出文件包括：

| 文件 | 路径 |
|---|---|
| Page embeddings | `artifacts/embeddings/full_multivector/pages/*.npy` |
| Page meta | `artifacts/embeddings/full_multivector/page_embedding_meta.jsonl` |
| Token stats JSON | `artifacts/embeddings/full_multivector/token_stats.json` |
| Token stats CSV | `artifacts/embeddings/full_multivector/token_stats.csv` |
| Page type stats | `artifacts/embeddings/full_multivector/token_stats_by_page_type.csv` |
| Run log | `artifacts/embeddings/full_multivector/page_embedding_run.log` |

---

## 5. Day 3：Query Embedding 与 Late Interaction Retrieval

### 5.1 目标

Day 3 的目标是完成 Full Multi-vector Retrieval 的小规模闭环，包括：

- query embedding 提取；
- page embedding 修正；
- late interaction scoring；
- run 文件输出；
- evaluation 评测。

---

### 5.2 Query Embedding 提取

Query embedding 提取完成情况如下：

| 项目 | 结果 |
|---|---:|
| Query 数量 | 30 |
| 表示方式 | Projected text token embeddings |
| Embedding dim | 512 |
| 输出目录 | `artifacts/embeddings/full_multivector/queries/` |

---

### 5.3 Page Embedding 空间修正

在 Day 3 中发现一个关键问题：

| 对象 | 初始维度 |
|---|---|
| Query embeddings | `(n, 512)` |
| Page embeddings | `(49, 768)` |

问题原因：

- Query embeddings 已经进入 CLIP shared projection space；
- Page embeddings 最初使用的是未投影的 visual hidden states；
- 二者不在同一向量空间中，无法直接计算相似度。

修正方式：

- 使用 CLIP `visual_projection` 后的 projected visual tokens；
- 将 page embeddings 从 `(49, 768)` 修正为 `(49, 512)`；
- 保证 page tokens 与 query tokens 位于同一 embedding space。

修正后：

| 对象 | 最终维度 |
|---|---|
| Query embeddings | `(n, 512)` |
| Page embeddings | `(49, 512)` |

---

### 5.4 Late Interaction Retrieval 跑通

使用 sum-maxsim scoring 成功生成 small subset run 文件：

| 类型 | 路径 |
|---|---|
| Small run | `results/full_multivector/full_mv_small_run.tsv` |
| Small metrics | `results/full_multivector/full_mv_small_metrics.json` |

---

### 5.5 Evaluation 问题修正

最初 evaluation 结果异常，主要问题包括：

1. Subset query 选中数为 0；
2. 配置字段名不一致；
3. Query/page embedding 维度不一致；
4. Evaluation 脚本错误地按 doc-level 比较，而 qrels 是 page-level。

最终修正后：

- qrels 按 page-level 读取；
- run 文件按 page_id 匹配；
- evaluation 输出恢复正常。

该问题很重要，因为它确认了后续所有主结果应以 **page-level retrieval** 为主口径，doc-level 只作为辅助分析。

---

## 6. Day 4：Full MV 正式实验与 Single-vector 对比

### 6.1 目标

Day 4 的目标是在正式实验规模上运行 Full Multi-vector Retrieval，并与基于同一套 projected embeddings 的 single-vector baseline 做系统对比。

---

### 6.2 Full MV 正式实验输出

| 类型 | 路径 |
|---|---|
| Full MV run | `results/full_multivector/full_mv_run.tsv` |
| Full MV metrics | `results/full_multivector/full_mv_metrics.json` |

---

### 6.3 Full MV Page-level 结果

| Metric | Full Multi-vector |
|---|---:|
| MRR@10 | 0.0644 |
| Recall@1 | 0.0333 |
| Recall@5 | 0.1000 |
| Recall@10 | 0.1333 |
| nDCG@10 | 0.0807 |

---

### 6.4 Full MV Doc-level 辅助结果

| Metric | Full Multi-vector |
|---|---:|
| Doc Recall@1 | 0.7333 |
| Doc Recall@5 | 0.9000 |
| Doc Recall@10 | 0.9000 |

该结果说明：

- Full MV 能较好定位相关文档；
- 但在文档内部精确定位目标页面仍然较弱；
- page-level retrieval 是当前主要瓶颈。

---

### 6.5 Single-vector Baseline 构建

Single-vector baseline 使用与 Full MV 相同的 projected embeddings 构建。

方法为：

- query token mean pooling；
- page token mean pooling；
- cosine / dot-product 排序。

输出文件：

| 类型 | 路径 |
|---|---|
| Single-vector run | `results/single_vector/single_vector_run.tsv` |
| Single-vector metrics | `results/single_vector/single_vector_metrics.json` |

---

### 6.6 Full MV vs Single-vector 对比

Page-level 对比如下：

| Method | MRR@10 | Recall@1 | Recall@5 | Recall@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Single-vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Full Multi-vector | 0.0644 | 0.0333 | 0.1000 | 0.1333 | 0.0807 |

Doc-level 辅助对比如下：

| Method | Doc Recall@1 | Doc Recall@5 | Doc Recall@10 |
|---|---:|---:|---:|
| Single-vector | 0.0333 | 0.7000 | 0.7333 |
| Full Multi-vector | 0.7333 | 0.9000 | 0.9000 |

---

### 6.7 阶段结论

Full Multi-vector 明显优于基于 mean pooling 的 single-vector baseline，说明局部 token-level matching 对 PCB 工程文档页面检索是有价值的。

但 Full MV 的 page-level 指标仍然低于 OCR + BM25，说明当前视觉方法还不能作为 standalone retriever 替代文本方法。

更合理的定位是：

> Full MV 是一种结构感知的视觉补充方法，适合用于 reranking、fusion 或 evidence attribution，而不是直接替代 OCR/BM25。

---

## 7. Day 5：成本分析

### 7.1 目标

Day 5 的目标是系统记录 Full Multi-vector 的存储和检索成本，并与 single-vector baseline 做性能—代价对照分析。

---

### 7.2 性能对比

| Method | MRR@10 | Recall@10 | nDCG@10 | Doc Recall@10 |
|---|---:|---:|---:|---:|
| Single-vector | 0.0000 | 0.0000 | 0.0000 | 0.7333 |
| Full Multi-vector | 0.0644 | 0.1333 | 0.0807 | 0.9000 |

---

### 7.3 成本对比

| Method | Vectors/Page | Vector Dim | Estimated Raw Index Size | Avg Query Latency |
|---|---:|---:|---:|---:|
| Single-vector | 1 | 512 | 0.1973 MB | 0.1130 ms |
| Full Multi-vector | 49 | 512 | 9.6660 MB | 6.5679 ms |

---

### 7.4 成本增长倍数

| 成本项 | Full MV 相比 Single-vector |
|---|---:|
| Vectors/Page | 49.0x |
| Index Size | 49.0x |
| Avg Query Latency | 58.1x |

---

### 7.5 成本分析结论

Full MV 相比 single-vector 带来了更强的视觉检索能力，但成本显著增加：

- 向量数量增加约 49 倍；
- 存储成本增加约 49 倍；
- 平均 query latency 增加约 58 倍。

这说明 Full MV 不适合直接全量部署为唯一检索器。后续必须研究 budgeted retrieval，包括：

- candidate budget；
- token budget；
- vector compression；
- coarse-to-fine retrieval；
- BM25 top-N + Full MV reranking。

---

## 8. 本阶段主要结论

Week 3 得到以下关键结论：

1. Full Multi-vector Retrieval 管线已经成功跑通。
2. Query/page embedding 空间不一致问题已修正。
3. Full MV 明显优于 projected single-vector baseline。
4. Full MV 在 doc-level 上表现较好，但 page-level 精确定位仍然不足。
5. Full MV 成本显著高于 single-vector。
6. 当前结果支持后续开展 budgeted multi-vector retrieval。
7. 视觉方法应定位为 OCR/Text 的结构补充和 reranking 信号，而不是直接替代文本检索。

---

## 9. 对论文叙事的影响

Week 3 实验支持以下论文叙事：

> Single-vector visual retrieval is insufficient for PCB engineering document retrieval because global page embeddings lose fine-grained local structures. Multi-vector late interaction improves visual retrieval by preserving local token-level evidence, but it introduces substantial storage and latency costs. Therefore, the key research problem becomes how to retain the fine-grained matching capability of multi-vector retrieval under practical budget constraints.

中文表述为：

> 单向量视觉检索难以表达 PCB 工程文档中的局部结构、表格、图例和细粒度标注。Multi-vector late interaction 能够通过 token-level matching 提升视觉检索能力，但也带来了显著的存储和计算成本。因此，后续研究重点应转向预算约束下的多向量检索优化。

---

## 10. 下一阶段实验方向

根据 Week 3 结果，后续实验建议优先开展：

### 10.1 BM25 Top-N + Full MV Reranking

使用 BM25 作为 coarse retriever，Full MV 只对 Top-N 候选页面进行重排。

候选规模建议：

| N | 目的 |
|---:|---|
| 10 | 极低成本 rerank |
| 20 | 小候选集实验 |
| 50 | 推荐主实验设置 |
| 100 | 接近全量上限 |

重点观察：

- Recall@10 是否保持；
- MRR 是否提升；
- nDCG@10 是否提升；
- latency 是否明显下降；
- BM25 与 Full MV 是否存在互补。

---

### 10.2 Token Budget Experiment

对每页视觉 token 做预算化选择，例如：

| Token Budget | 含义 |
|---:|---|
| 4 | 极低预算 |
| 8 | 小预算 |
| 16 | 中等预算 |
| 32 | 高预算 |
| 49 | Full MV 上限 |

目标是绘制 performance-cost trade-off 曲线。

---

### 10.3 Fusion Experiment

探索文本分数与视觉分数融合，例如：

- BM25 score + Full MV score；
- Dense score + Full MV score；
- BM25 + Dense + Full MV。

该实验用于验证文本和视觉信号是否互补。

---

## 11. 可写入论文的阶段性表述

Week 3 implements the proposed full multi-vector late interaction retrieval pipeline. Each PCB document page is represented as a set of projected visual token embeddings, while each query is represented using token-level text embeddings in the same CLIP projection space. The retrieval score is computed using a sum-maxsim late interaction function. Compared with a single-vector baseline built from the same projected embeddings, full multi-vector retrieval achieves substantially better page-level and document-level performance, demonstrating the benefit of local token-level matching. However, this improvement comes with a significant cost: the number of vectors, raw index size, and query latency increase by approximately 49x, 49x, and 58x respectively. These findings motivate the next stage of budgeted multi-vector retrieval and coarse-to-fine reranking.
